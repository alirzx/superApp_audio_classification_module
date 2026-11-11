"""Pinned-release downloader; production requires a separately obtained expected SHA256."""
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from app.core.config import RELEASE,RELEASE_BASE,ModelSetupSettings
from app.core.model_integrity import sha256,verify_model

def main():
    settings=ModelSetupSettings()
    dest=settings.model_dir
    expected=settings.expected_model_sha256.lower()
    dest.mkdir(parents=True,exist_ok=True)
    if settings.checkpoint.exists() and settings.manifest.exists():
        manifest=verify_model(settings)
        if expected and manifest["sha256"]!=expected:
            raise RuntimeError("Cached model SHA256 does not match expected digest")
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
        if expected and digest!=expected: raise RuntimeError("Expected model SHA256 mismatch")
        os.chmod(tmp,0o644)
        os.replace(tmp,settings.checkpoint)
        manifest={"name":settings.model_name,
            "filename":settings.model_spec["filename"],"release":RELEASE,"url":url,
            "size":settings.model_spec["size"],"sha256":digest}
        with tempfile.NamedTemporaryFile(prefix=".manifest-",dir=dest,
                                         mode="w",encoding="utf-8",delete=False) as mf:
            manifest_tmp=Path(mf.name)
            try:
                json.dump(manifest,mf,indent=2)
                mf.write("\n")
                mf.flush()
                os.fsync(mf.fileno())
                os.chmod(manifest_tmp,0o644)
            except Exception:
                manifest_tmp.unlink(missing_ok=True)
                raise
        os.replace(manifest_tmp,settings.manifest)
        print("Model verified and cached:",settings.model_name,digest)
    finally:
        tmp.unlink(missing_ok=True)

if __name__=="__main__": main()
