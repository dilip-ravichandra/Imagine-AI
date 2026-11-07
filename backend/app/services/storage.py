"""Safe image storage. Filenames are server-generated hex ids; client input never reaches a path."""
import os
import re
from pathlib import Path

_ID = re.compile(r"^[0-9a-f]{32}$")


class ImageStore:
    def __init__(self, directory: Path, max_files: int = 200):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.max_files = max_files

    def save(self, image, image_id: str) -> str:
        if not _ID.match(image_id):
            raise ValueError("invalid image id")
        name = f"{image_id}.png"
        tmp = self.directory / f".{image_id}.tmp"
        image.save(tmp, format="PNG")
        os.replace(tmp, self.directory / name)  # atomic: never serve a half-written file
        self._prune(keep=name)
        return name

    def _prune(self, keep: str) -> None:
        """Delete oldest images beyond max_files. Never deletes `keep` (the file just saved),
        even if timestamps tie (coarse mtime resolution on some filesystems)."""
        if self.max_files <= 0:
            return
        others = sorted((p for p in self.directory.glob("*.png") if p.name != keep),
                        key=lambda p: p.stat().st_mtime)
        for old in others[:max(0, len(others) + 1 - self.max_files)]:
            old.unlink(missing_ok=True)
