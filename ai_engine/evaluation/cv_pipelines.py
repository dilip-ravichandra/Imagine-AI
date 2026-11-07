"""CV post-processing used by the CV-on variant. Only what exists today (P5A); P5B will register its pipeline here."""
from typing import Callable

from computer_vision import to_array, to_pil
from computer_vision.enhancement import EnhanceConfig, auto_enhance


def p5a_auto_enhance(pil_image):
    """Returns (PIL image, applied, notes). applied=False means the dead band bypassed it (image unchanged)."""
    res = auto_enhance(to_array(pil_image), EnhanceConfig())
    return to_pil(res.image), res.applied, list(res.notes)


PIPELINES: dict[str, Callable] = {"p5a_auto_enhance": p5a_auto_enhance}
