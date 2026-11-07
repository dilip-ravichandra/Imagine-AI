"""Artifact FLAGS from quality measurements. Flags say 'this measurement is outside its band', not 'this image is bad'.

ALL thresholds are PROVISIONAL: they were chosen by looking at synthetic degradations and have NOT been checked on
real SD-Turbo output. A flag can be a false alarm for an intentional look (night scene, underwater tint, soft focus);
`suppress` exists so the caller can silence flags the prompt asked for.
"""
from dataclasses import dataclass, field
from typing import Iterable, Optional

import numpy as np

from ..common import validate_image
from ..quality import QualityReport, assess_quality

# flag name -> (human note, correctable by the conservative classical correction in correct.py)
FLAGS = {
    "blur": ("soft / out of focus (re-blur ratio high on an image that has edges)", True),
    "noise": ("high-frequency noise (estimated sigma above band)", True),
    "dark": ("mean brightness below band", True),
    "bright": ("mean brightness above band", True),
    "low_contrast": ("luma spread below band", True),
    "colour_cast": ("channel means deviate from each other (gray-world); wrong for single-colour scenes", True),
    "clipped_shadows": ("many pixels crushed to black; detail is lost, filters cannot restore it", False),
    "clipped_highlights": ("many pixels blown to white; detail is lost, filters cannot restore it", False),
    "halo": ("ringing/overshoot beside hard edges; not corrected here (avoid unsharp masking, or regenerate)", False),
}


@dataclass(frozen=True)
class ArtifactThresholds:
    blur_ratio_min: float = 0.33
    blur_min_gradient: float = 4.0  # gradient_p99 below this = no structure (flat / smooth sky): do not call it blurry
    noise_sigma_max: float = 5.0  # 0..255 scale, per channel
    brightness_min: float = 0.20
    brightness_max: float = 0.85
    contrast_min: float = 0.06
    colour_cast_max: float = 0.22
    clipped_dark_max: float = 0.20
    clipped_bright_max: float = 0.08
    halo_score_max: float = 0.25  # needs >= 20 evaluated edges (else the metric reports 0 = no evidence)


@dataclass(frozen=True)
class ArtifactFlag:
    name: str
    value: float
    threshold: float
    correctable: bool
    note: str


@dataclass(frozen=True)
class ArtifactReport:
    quality: QualityReport
    flags: tuple[ArtifactFlag, ...]
    suppressed: tuple[str, ...] = field(default_factory=tuple)  # would have been flagged but caller asked to ignore

    @property
    def names(self) -> list[str]:
        return [f.name for f in self.flags]


def flags_from_quality(q: QualityReport, t: ArtifactThresholds) -> list[ArtifactFlag]:
    checks = [
        ("blur", q.blur_ratio, t.blur_ratio_min, q.blur_ratio > t.blur_ratio_min and q.gradient_p99 >= t.blur_min_gradient),
        ("noise", q.noise_sigma, t.noise_sigma_max, q.noise_sigma > t.noise_sigma_max),
        ("dark", q.brightness, t.brightness_min, q.brightness < t.brightness_min),
        ("bright", q.brightness, t.brightness_max, q.brightness > t.brightness_max),
        ("low_contrast", q.contrast, t.contrast_min, q.contrast < t.contrast_min),
        ("colour_cast", q.colour_cast, t.colour_cast_max, q.colour_cast > t.colour_cast_max),
        ("clipped_shadows", q.clipped_dark, t.clipped_dark_max, q.clipped_dark >= t.clipped_dark_max),
        ("clipped_highlights", q.clipped_bright, t.clipped_bright_max, q.clipped_bright >= t.clipped_bright_max),
        ("halo", q.halo_score, t.halo_score_max, q.halo_edges >= 20 and q.halo_score >= t.halo_score_max),
    ]
    return [ArtifactFlag(n, float(v), float(th), FLAGS[n][1], FLAGS[n][0]) for n, v, th, hit in checks if hit]


def detect_artifacts(image: np.ndarray, thresholds: Optional[ArtifactThresholds] = None,
                     suppress: Iterable[str] = (), quality: Optional[QualityReport] = None) -> ArtifactReport:
    """Measure (or reuse `quality`) and flag. Unknown names in `suppress` raise ValueError (typos must not pass silently)."""
    suppress = frozenset(suppress)
    unknown = suppress - set(FLAGS)
    if unknown:
        raise ValueError(f"unknown flag names in suppress: {sorted(unknown)}")
    q = quality if quality is not None else assess_quality(validate_image(image))
    hits = flags_from_quality(q, thresholds or ArtifactThresholds())
    return ArtifactReport(quality=q, flags=tuple(f for f in hits if f.name not in suppress),
                          suppressed=tuple(f.name for f in hits if f.name in suppress))
