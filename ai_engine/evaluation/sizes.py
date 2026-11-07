"""Model/adapter/artifact size report (EVAL-05). File sizes on disk; parameter count is NOT download size."""
import os
from pathlib import Path
from typing import Optional

WEIGHT_SUFFIXES = (".safetensors", ".bin", ".ckpt", ".pt", ".pth", ".onnx", ".gguf")


def path_size_bytes(path: Path) -> int:
    p = Path(path)
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())  # follows symlinked blobs via stat()


def hf_hub_dir() -> Path:
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    return home / "hub"


def find_hf_snapshot(model_id: str, revision: Optional[str], hub_dir: Optional[Path] = None) -> Optional[Path]:
    """Locate the cached snapshot dir of `model_id` at `revision` (exact commit hash). None if not cached.
    Without a revision the result would be ambiguous, so None is returned rather than guessing."""
    if not revision:
        return None
    snap = (hub_dir or hf_hub_dir()) / ("models--" + model_id.replace("/", "--")) / "snapshots" / revision
    return snap if snap.is_dir() else None


def size_report(model_dir: Optional[Path] = None, adapter_path: Optional[Path] = None,
                extra: Optional[dict] = None) -> dict:
    """Bytes per category. Missing inputs stay None (never estimated). `weights` lists weight files only, so fp16 and
    fp32 variants of the same checkpoint are visible separately; `total_dir_bytes` is everything in the snapshot."""
    rep = {"base_total_dir_bytes": None, "base_weight_files": None, "adapter_bytes": None, "extra": {}}
    if model_dir is not None and Path(model_dir).exists():
        d = Path(model_dir)
        rep["base_total_dir_bytes"] = path_size_bytes(d)
        rep["base_weight_files"] = {f.relative_to(d).as_posix(): f.stat().st_size
                                    for f in sorted(d.rglob("*")) if f.is_file() and f.suffix in WEIGHT_SUFFIXES}
    if adapter_path is not None and Path(adapter_path).exists():
        rep["adapter_bytes"] = path_size_bytes(Path(adapter_path))
    for name, p in (extra or {}).items():
        rep["extra"][name] = path_size_bytes(Path(p)) if Path(p).exists() else None
    return rep
