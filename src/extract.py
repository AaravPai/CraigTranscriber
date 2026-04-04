from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


def extract_zip(zip_path: Path, destination_dir: Path) -> Path:
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    if destination_dir.exists():
        shutil.rmtree(destination_dir)

    destination_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(destination_dir)

    return destination_dir