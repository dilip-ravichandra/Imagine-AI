"""Builds the P6 controller from settings. Returns (None, None) when ADAPTIVE_PROFILE is not set (controller OFF).

Any problem with a configured profile/policy raises at startup: a misconfigured controller must never silently
fall back to the old fixed mode->steps mapping.
"""
import json
import threading
from typing import Optional

from ai_engine.adaptive import (AdaptiveController, ControllerPolicy, ResourceMonitor, SystemMonitor,
                                load_policy, load_profile_set)

from ..config import Settings


class JsonlSink:
    """Appends one JSON line per controller decision. Contains no prompt text (only configs and numbers)."""

    def __init__(self, path):
        self.path, self._lock = path, threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, record: dict) -> None:
        line = json.dumps(record, sort_keys=True, default=str)
        with self._lock, open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def build_controller(settings: Settings) -> tuple[Optional[AdaptiveController], Optional[ResourceMonitor]]:
    if settings.adaptive_profile is None:
        return None, None
    profile = load_profile_set(settings.adaptive_profile)
    if profile.synthetic and not settings.adaptive_allow_synthetic:
        raise ValueError("ADAPTIVE_PROFILE is marked synthetic (not measured). Build a real profile with "
                         "evaluation/scripts/build_adaptive_profile.py, or set ADAPTIVE_ALLOW_SYNTHETIC=true "
                         "for a demo.")
    policy = load_policy(settings.adaptive_policy) if settings.adaptive_policy else ControllerPolicy()
    sink = JsonlSink(settings.adaptive_decision_log) if settings.adaptive_decision_log else None
    return AdaptiveController(profile, policy, log_sink=sink), SystemMonitor()
