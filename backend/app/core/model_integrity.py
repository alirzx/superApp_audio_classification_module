import hashlib
import json
from pathlib import Path
from .config import RELEASE, RELEASE_BASE, ModelSetupSettings

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""): h.update(block)
    return h.hexdigest()

def verify_model(settings: ModelSetupSettings) -> dict:
    """Check cached release artifact and TOFU manifest; independent SHA pin needed for production bootstrap."""
    if not settings.checkpoint.is_file() or not settings.manifest.is_file():
        raise RuntimeError("Model unprepared: run model-setup")
    manifest=json.loads(settings.manifest.read_text(encoding="utf-8"))
    expected={"name":settings.model_name,"filename":settings.model_spec["filename"],
              "size":settings.model_spec["size"],"release":RELEASE,
              "url":RELEASE_BASE+settings.model_spec["filename"]}
    if any(manifest.get(k)!=v for k,v in expected.items()): raise RuntimeError("Model manifest identity mismatch")
    if settings.checkpoint.stat().st_size!=expected["size"]: raise RuntimeError("Model size mismatch")
    if not isinstance(manifest.get("sha256"),str) or len(manifest["sha256"])!=64:
        raise RuntimeError("Missing model checksum")
    if settings.expected_model_sha256 and manifest["sha256"].lower()!=settings.expected_model_sha256.lower():
        raise RuntimeError("Model SHA256 does not match independently pinned digest")
    if sha256(settings.checkpoint)!=manifest["sha256"]: raise RuntimeError("Model checksum mismatch")
    return manifest
