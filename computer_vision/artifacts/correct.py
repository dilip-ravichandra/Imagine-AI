"""Conservative, re-assessed correction. One mild step per correctable flag; each step is KEPT only if its target
measurement moves the right way by a margin AND it creates no new flag; otherwise it is discarded and the reason recorded.
This guards against filters that fix one number while breaking another. It proves the NUMBER moved, not that a person
would find the picture better. Un-correctable flags (clipping, halo) and semantic defects are reported, never 'fixed'."""
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

import numpy as np

from ..common import validate_image
from ..edge_aware import bilateral_smooth, edge_preserving_sharpen
from ..enhancement import EnhanceConfig, apply_clahe, auto_enhance, white_balance_gray_world
from ..quality import QualityReport, assess_quality
from .detect import ArtifactReport, ArtifactThresholds, detect_artifacts

MIN_RELATIVE_GAIN = 0.10  # target measurement must improve by at least 10 %


@dataclass(frozen=True)
class StepRecord:
    name: str
    flag: str
    accepted: bool
    reason: str
    target_before: float
    target_after: Optional[float]


@dataclass
class CorrectionResult:
    image: np.ndarray
    applied: bool  # True iff at least one step was accepted
    steps: list[StepRecord] = field(default_factory=list)
    before: Optional[ArtifactReport] = None
    after: Optional[ArtifactReport] = None
    notes: list[str] = field(default_factory=list)


def _band_distance(v: float, lo: float, hi: float) -> float:
    return max(lo - v, v - hi, 0.0)


def _steps(t: ArtifactThresholds):
    """(step name, flag, apply(img, q) -> image, target(q) -> value, improved(before, after) -> bool)."""
    rel = lambda b, a: a <= b * (1 - MIN_RELATIVE_GAIN)  # lower is better
    return [
        ("denoise", "noise",
         lambda im, q: bilateral_smooth(im, d=7, sigma_color=float(np.clip(3 * q.noise_sigma, 15, 40)), sigma_space=5.0).image,
         lambda q: q.noise_sigma, rel),
        ("white_balance", "colour_cast",
         lambda im, q: white_balance_gray_world(im, strength=0.6, max_gain=1.25).image,
         lambda q: q.colour_cast, rel),
        ("exposure", "dark",
         lambda im, q: auto_enhance(im, EnhanceConfig(white_balance=False, contrast=False)).image,
         lambda q: _band_distance(q.brightness, t.brightness_min, t.brightness_max),
         lambda b, a: a <= b * (1 - MIN_RELATIVE_GAIN)),
        ("exposure", "bright",
         lambda im, q: auto_enhance(im, EnhanceConfig(white_balance=False, contrast=False)).image,
         lambda q: _band_distance(q.brightness, t.brightness_min, t.brightness_max),
         lambda b, a: a <= b * (1 - MIN_RELATIVE_GAIN)),
        ("contrast", "low_contrast",
         lambda im, q: apply_clahe(im, clip_limit=1.5, strength=0.5).image,
         lambda q: q.contrast, lambda b, a: a >= b * (1 + MIN_RELATIVE_GAIN)),
        ("sharpen", "blur",
         lambda im, q: edge_preserving_sharpen(im, amount=0.6, radius=1.5).image,
         lambda q: q.blur_ratio, rel),
    ]


def correct_artifacts(image: np.ndarray, thresholds: Optional[ArtifactThresholds] = None,
                      suppress: Iterable[str] = (), enabled: bool = True) -> CorrectionResult:
    """Order: denoise -> white balance -> exposure -> contrast -> sharpen. Returns the input unchanged (copy) when
    disabled, when nothing correctable is flagged, or when every step was rejected."""
    img = validate_image(image)
    t = thresholds or ArtifactThresholds()
    suppress = frozenset(suppress)
    before = detect_artifacts(img, t, suppress)
    res = CorrectionResult(image=img.copy(), applied=False, before=before, after=before)
    if not enabled:
        res.notes.append("disabled")
        return res
    cur, cur_report = img, before
    done_exposure = False
    for name, flag, apply, target, improved in _steps(t):
        if flag not in cur_report.names or (name == "exposure" and done_exposure):
            continue
        if name == "exposure":
            done_exposure = True
        t_before = target(cur_report.quality)
        cand = apply(cur, cur_report.quality)
        cand_report = detect_artifacts(cand, t, suppress)
        new = set(cand_report.names) - set(cur_report.names)
        if name == "denoise":
            new.discard("blur")  # smoothing may soften; the sharpen step that follows is judged on its own
        t_after = target(cand_report.quality)
        if new:
            res.steps.append(StepRecord(name, flag, False, f"rejected: introduced {sorted(new)}", t_before, t_after))
        elif not improved(t_before, t_after):
            res.steps.append(StepRecord(name, flag, False, "rejected: target measurement did not improve enough", t_before, t_after))
        else:
            res.steps.append(StepRecord(name, flag, True, "accepted", t_before, t_after))
            cur, cur_report, res.applied = cand, cand_report, True
    res.image, res.after = (cur.copy() if res.applied else img.copy()), cur_report
    remaining = [f for f in cur_report.flags if not f.correctable]
    if remaining:
        res.notes.append("not correctable by filters, left flagged: " + ", ".join(f.name for f in remaining))
    return res
