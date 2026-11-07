"""Orchestrates one generation: validate -> single-flight guard -> engine -> store -> response."""
import logging
import secrets
import sys
import threading
import time
import uuid
from typing import Optional

from ai_engine.adaptive import ControllerRequest, ResourceError, run_with_fallback
from ai_engine.prompt import PromptAnalysis, analyze_prompt

from ..config import Settings
from ..schemas.v1 import (GenerateRequest, GenerateResponse, GenerationInfo, PerformanceInfo,
                          QualityInfo, ResourceDecision)
from .engine import DiffusionEngine
from .errors import ServiceError, busy, engine_unavailable, no_safe_configuration, unsupported_resolution
from .storage import ImageStore

log = logging.getLogger("imagineai.generation")

# Provisional mapping (SD-Turbo supports 1-4 steps). NOT benchmarked; P4/P6 will replace it with measured profiles.
MODE_STEPS = {"quick": 1, "balanced": 2, "best": 4}


def process_peak_ram_mb() -> Optional[float]:
    """Peak resident memory of this server process since start (includes model load), or None."""
    try:
        if sys.platform == "win32":
            import psutil
            return psutil.Process().memory_info().peak_wset / 1048576
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak / 1048576 if sys.platform == "darwin" else peak / 1024
    except Exception:  # noqa: BLE001
        return None


class GenerationService:
    def __init__(self, engine: DiffusionEngine, store: ImageStore, settings: Settings,
                 controller=None, monitor=None):
        self.engine, self.store, self.settings = engine, store, settings
        # P6: controller=None (default) keeps the fixed MODE_STEPS behaviour exactly as before.
        self.controller, self.monitor = controller, monitor
        self._busy = threading.Lock()  # one load/generation at a time (8 GB VRAM laptop)

    @staticmethod
    def analyze(prompt: str) -> Optional[PromptAnalysis]:
        """Structured prompt analysis. A parser failure must never break generation, so errors return None."""
        try:
            return analyze_prompt(prompt)
        except Exception:  # noqa: BLE001
            log.exception("prompt analysis failed; continuing without it")
            return None

    def _run_cv(self, pil_image, prompt: str, analysis: Optional[PromptAnalysis]):
        """P5B hook. Returns (QualityInfo | None, cv_ms | None, image). A CV failure must never break generation:
        on any error the ORIGINAL image is used and quality/cv_ms are None."""
        try:
            from computer_vision import CVPipelineConfig, run_pipeline, to_array, to_pil  # lazy: CV deps optional when off
            from computer_vision.artifacts import intent_suppressions, semantic_review
            semantic, suppress = None, frozenset()
            if analysis is not None:
                objs = analysis.objects
                semantic = semantic_review([o.name for o in objs], [o.count for o in objs],
                                           sum(1 for r in analysis.relations if r.spatial),
                                           sum(1 for o in objs if o.attributes))
                suppress = intent_suppressions(prompt, [t.value for t in analysis.lighting],
                                               [e.name for e in analysis.environment])
            cfg = CVPipelineConfig(assess=True, correct=self.settings.cv_mode == "correct", suppress=suppress)
            r = run_pipeline(to_array(pil_image), cfg, semantic)
            q = (r.report_after or r.report_before).quality
            quality = QualityInfo(sharpness=q.sharpness, brightness=q.brightness, contrast=q.contrast,
                                  artifact_flags=r.flag_names)
            return quality, r.cv_ms, (to_pil(r.image) if r.changed else pil_image)
        except Exception:  # noqa: BLE001
            log.exception("CV stage failed; serving the original image")
            return None, None, pil_image

    def generate(self, req: GenerateRequest, base_url: str, request_id: str) -> GenerateResponse:
        if req.resolution not in self.settings.supported_resolutions:  # client errors before server errors
            raise unsupported_resolution(self.settings.supported_resolutions)
        ok, reason = self.engine.availability()
        if not ok:
            raise engine_unavailable(reason)
        seed = req.seed if req.seed is not None else secrets.randbelow(2**32)
        steps = MODE_STEPS[req.quality_mode]
        # P2 INTEGRATION HOOK. The engine below always receives the RAW prompt, unchanged: SD-Turbo was not
        # validated on rewritten prompts, so feeding it analysis output would be an unproven change.
        # `analysis` is for logging now; P3B/P6 may read it (e.g. analysis.complexity) once evidence supports it.
        analysis = self.analyze(req.prompt)
        if analysis is not None:
            log.info("request=%s prompt_analysis objects=%d relations=%d level=%s ambiguities=%d", request_id,
                     analysis.complexity.object_count, analysis.complexity.relation_count,
                     analysis.complexity.level, len(analysis.ambiguities))
        if not self._busy.acquire(blocking=False):
            raise busy()
        try:
            load_ms = self.engine.ensure_loaded()  # measured separately; not part of end_to_end_ms
            t0 = time.perf_counter()
            execution = None
            if self.controller is None:
                res = self.engine.generate(req.prompt, seed, req.resolution, req.resolution, steps)
            else:  # P6: controller picks (and may fall back) the configuration
                execution = self._generate_adaptive(req, seed, analysis)
                res = execution.value
            quality, cv_ms, image = None, None, res.image
            if self.settings.cv_mode != "off":  # P5B: assess/correct AFTER generation; original kept on any CV error
                quality, cv_ms, image = self._run_cv(res.image, req.prompt, analysis)
            self.store.save(image, request_id)
            end_to_end_ms = (time.perf_counter() - t0) * 1000.0
        finally:
            self._busy.release()
        base = self.settings.public_base_url or base_url.rstrip("/")
        if execution is not None:
            decision = ResourceDecision(**execution.to_resource_decision())
        else:
            decision = ResourceDecision(
                fallback_used=False, reason=None,
                explanation=(f"{req.quality_mode} mode -> {res.steps} step(s) at "
                             f"{res.width}x{res.height}. No adaptive controller yet (P6); "
                             "no fallback applied."))
        return GenerateResponse(
            request_id=request_id,
            image_url=f"{base}/images/{request_id}.png",
            generation=GenerationInfo(model=res.model, model_revision=res.model_revision,
                                      precision=res.precision, scheduler=res.scheduler,
                                      steps=res.steps, width=res.width, height=res.height,
                                      seed=res.seed),
            performance=PerformanceInfo(model_load_ms=load_ms, cv_ms=cv_ms, end_to_end_ms=end_to_end_ms,
                                        peak_gpu_mb=res.peak_gpu_mb,
                                        peak_process_ram_mb=process_peak_ram_mb()),
            quality=quality,
            resource_decision=decision,
        )

    def _locked_runtime(self) -> dict:
        """Settings the already-loaded engine cannot change without a reload; the controller may not pick
        a configuration that needs a different value."""
        info = getattr(self.engine, "load_info", None) or {}
        lock = {"model_id": self.settings.model_id, "attention_slicing": self.settings.attention_slicing,
                "vae_slicing": self.settings.vae_slicing, "offload": self.settings.offload}
        for k in ("precision", "device"):
            if info.get(k):
                lock[k] = info[k]
        return lock

    def _generate_adaptive(self, req: GenerateRequest, seed: int, analysis: Optional[PromptAnalysis]):
        level = analysis.complexity.level if analysis is not None else None
        creq = ControllerRequest(quality_mode=req.quality_mode, resolution=req.resolution,
                                 complexity_level=level, locked_runtime=self._locked_runtime(),
                                 allow_remote=False)  # remote/hybrid backends need explicit consent UI (not built)
        try:
            return run_with_fallback(
                self.controller, creq, self.monitor,
                lambda e: self.engine.generate(req.prompt, seed, e.resolution, e.resolution, e.steps))
        except ResourceError as exc:
            log.warning("request: no safe configuration (%s)", exc.message)
            raise no_safe_configuration("No generation configuration fits the currently available resources.",
                                        exc.suggested_action) from None

    def preload(self) -> None:
        """Warm the model (used by PRELOAD_MODEL=true). Holds the guard so requests get a retryable 429."""
        with self._busy:
            self.engine.ensure_loaded()
