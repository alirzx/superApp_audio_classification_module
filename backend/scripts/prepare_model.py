"""Pinned-release downloader; production requires a separately obtained expected SHA256."""
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from app.core.config import RELEASE,RELEASE_BASE,Settings
from app.core.model_integrity import sha256,verify_model

def main():
    settings=Settings()
    dest=settings.model_dir
    dest.mkdir(parents=True,exist_ok=True)
    if settings.checkpoint.exists() and settings.manifest.exists():
        verify_model(settings)
        print("Existing verified model:",settings.model_name)
        return
    url=RELEASE_BASE+settings.model_spec["filename"]
    with tempfile.NamedTemporaryFile(prefix=".download-",dir=dest,delete=False) as fd:
        tmp=Path(fd.name)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"SuperApp-Audio/1.0"}),timeout=120) as response, tmp.open("wb") as out:
            while data:=response.read(1024*1024):
                out.write(data)
                if out.tell()>settings.model_spec["size"]: raise RuntimeError("Unexpected downloaded model size")
        if tmp.stat().st_size!=settings.model_spec["size"]: raise RuntimeError("Model file size mismatch")
        digest=sha256(tmp)
        expected=os.environ.get("EXPECTED_MODEL_SHA256","").strip().lower()
        if settings.app_env=="production" and not expected:
            raise RuntimeError("Production requires an independently verified EXPECTED_MODEL_SHA256")
        if expected and digest!=expected: raise RuntimeError("Expected model SHA256 mismatch")
        tmp.replace(settings.checkpoint)
        settings.manifest.write_text(json.dumps({"name":settings.model_name,
            "filename":settings.model_spec["filename"],"release":RELEASE,"url":url,
            "size":settings.model_spec["size"],"sha256":digest},indent=2)+"\n")
        print("Model verified and cached:",settings.model_name,digest)
    finally:
        tmp.unlink(missing_ok=True)

if __name__=="__main__": main()
