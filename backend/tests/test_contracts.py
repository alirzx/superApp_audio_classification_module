import json
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.audio.preprocessing import segment_audio
from app.audio.validation import InvalidAudio,check_upload
from app.core.config import Settings,RELEASE,RELEASE_BASE
from app.core.model_integrity import sha256,verify_model
from app.main import create_app

def test_segments_final_padding():
    audio=np.ones(11*32000,dtype=np.float32)
    parts=list(segment_audio(audio,10))
    assert len(parts)==2
    assert (parts[0][0],parts[0][1])==(0,10)
    assert (parts[1][0],parts[1][1])==(10,11)
    assert len(parts[1][2])==320000
    assert np.all(parts[1][2][32000:]==0)

def test_upload_validation():
    check_upload(b"123","hello.mp3",100)
    with pytest.raises(InvalidAudio): check_upload(b"123","hello.exe",100)
    with pytest.raises(InvalidAudio): check_upload(b"123","hello.wav",2)

def test_model_integrity(tmp_path):
    settings=Settings(app_env="test",model_dir=tmp_path)
    settings.checkpoint.write_bytes(b"x")
    manifest={"name":settings.model_name,"filename":settings.model_spec["filename"],
              "release":RELEASE,"url":RELEASE_BASE+settings.model_spec["filename"],
              "size":settings.model_spec["size"],"sha256":sha256(settings.checkpoint)}
    settings.manifest.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError,match="size"): verify_model(settings)
    settings.checkpoint.unlink()
    with pytest.raises(RuntimeError,match="unprepared"): verify_model(settings)

def test_oversized_request():
    class FakeEngine:
        ready=False
        labels=[str(i) for i in range(527)]
        def __init__(self,settings):pass
        def initialize(self):self.ready=True
    settings=Settings(app_env="test",max_upload_mb=1,max_request_bytes=1100000)
    with TestClient(create_app(settings,FakeEngine)) as client:
        response=client.post("/v1/classify",content=b"a"*1100001,
                             headers={"Content-Type":"application/octet-stream"})
        assert response.status_code==413,response.text
