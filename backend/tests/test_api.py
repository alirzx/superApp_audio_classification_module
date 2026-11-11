import io
import wave
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings

class FakeEngine:
    def __init__(self, settings):
        self.labels=[f"Class {i}" for i in range(527)]
        self.ready=False
    def initialize(self): self.ready=True
    def predict(self,samples):
        assert len(samples)==320000
        result=[0.0]*527
        result[5]=.86
        result[17]=.62
        return result

def sample_audio():
    buff=io.BytesIO()
    with wave.open(buff,"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(32000)
        wf.writeframes(np.zeros(32000,dtype="<i2").tobytes())
    return buff.getvalue()

@pytest.fixture
def client():
    app=create_app(Settings(app_env="test",api_token="secret",model_dir="/tmp/no-model"),FakeEngine)
    with TestClient(app) as c: yield c

def test_auth_and_health(client):
    assert client.get("/health/ready").json()["status"]=="ready"
    assert client.get("/v1/models").status_code==401
    assert len(client.get("/v1/labels",headers={"X-API-Key":"secret"}).json()["labels"])==527

def test_classify(client):
    r=client.post("/v1/classify",headers={"X-API-Key":"secret"},
                  files={"file":("sample.wav",sample_audio(),"audio/wav")},
                  data={"threshold":".5","top_k":"2"})
    assert r.status_code==200,r.text
    data=r.json()
    assert len(data["predictions"])==2
    assert data["predictions"][0]["label_id"]==5
    assert data["audio"]["windows"]==1

def test_invalid(client):
    assert client.post("/v1/classify",headers={"X-API-Key":"secret"},
        files={"file":("invalid.wav",b"bad")}).status_code==422
    assert client.post("/v1/classify",headers={"X-API-Key":"secret"},
        files={"file":("invalid.exe",sample_audio())}).status_code==422
    assert client.post("/v1/classify",headers={"X-API-Key":"secret"},
        files={"file":("sample.wav",sample_audio())},data={"top_k":"500"}).status_code==422

def test_settings():
    with pytest.raises(ValueError): Settings(app_env="production",api_token="")
    with pytest.raises(ValueError): Settings(app_env="test",model_name="unknown")
