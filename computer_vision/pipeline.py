"""Optional CV pipeline with per-stage toggles. Default config: measure only, change nothing.

Order: resize -> enhance (P5A auto_enhance) -> smooth (P5A bilateral) -> sharpen (P5A) -> correct (P5B guarded, re-assessed).
`enhance/smooth/sharpen` are the plain P5A stages (no re-assessment; for experiments). `correct` is the guarded one
meant for the service. Any stage can be off; with everything off the image is returned unchanged.
"""
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .artifacts import (ArtifactReport, ArtifactThresholds, CorrectionResult, SemanticReview, correct_artifacts,
                        detect_artifacts)
from .common import CVResult, validate_image
from .edge_aware import bilateral_smooth, edge_preserving_sharpen
from .enhancement import auto_enhance
from .resize import fit_to_resolution


@dataclass(frozen=True)
class CVPipelineConfig:
    assess: bool = True  # measure before/after and flag
    resolution: Optional[int] = None  # square letterbox resize; None = skip
    enhance: bool = False
    smooth: bool = False
    sharpen: bool = False
    correct: bool = False
    thresholds: ArtifactThresholds = field(default_factory=ArtifactThresholds)
    suppress: frozenset = frozenset()  # flag names the caller wants ignored (e.g. from intent_suppressions)


@dataclass
class PipelineResult:
    image: np.ndarray
    changed: bool  # any stage altered the pixels
    stages: list = field(default_factory=list)  # CVResult / CorrectionResult per stage that ran
    report_before: Optional[ArtifactReport] = None
    report_after: Optional[ArtifactReport] = None
    semantic: Optional[SemanticReview] = None
    cv_ms: float = 0.0
    notes: list = field(default_factory=list)

    @property
    def flag_names(self) -> list[str]:
        """Pixel flags of the FINAL image (+ the semantic recommendation when present)."""
        base = list((self.report_after or self.report_before).names) if (self.report_after or self.report_before) else []
        if self.semantic is not None and self.semantic.recommended:
            from .artifacts import SEMANTIC_FLAG
            base.append(SEMANTIC_FLAG)
        return base


def run_pipeline(image: np.ndarray, config: Optional[CVPipelineConfig] = None,
                 semantic: Optional[SemanticReview] = None) -> PipelineResult:
    cfg = config or CVPipelineConfig()
    img = validate_image(image)
    t0 = time.perf_counter()
    res = PipelineResult(image=img.copy(), changed=False, semantic=semantic)
    cur = img
    if cfg.assess:
        res.report_before = detect_artifacts(cur, cfg.thresholds, cfg.suppress)

    simple = [(cfg.resolution is not None, lambda x: fit_to_resolution(x, cfg.resolution, mode="pad")),
              (cfg.enhance, auto_enhance),
              (cfg.smooth, lambda x: bilateral_smooth(x, strength=0.5)),
              (cfg.sharpen, lambda x: edge_preserving_sharpen(x, amount=0.6))]
    for on, fn in simple:
        if on:
            r: CVResult = fn(cur)
            res.stages.append(r)
            cur = r.image
            res.changed = res.changed or r.applied
    if cfg.correct:
        c: CorrectionResult = correct_artifacts(cur, cfg.thresholds, cfg.suppress)
        res.stages.append(c)
        cur = c.image
        res.changed = res.changed or c.applied
        res.report_after = c.after
    elif cfg.assess:
        res.report_after = detect_artifacts(cur, cfg.thresholds, cfg.suppress) if res.changed else res.report_before
    res.image = cur.copy() if res.changed else img.copy()
    res.cv_ms = (time.perf_counter() - t0) * 1000.0
    return res
