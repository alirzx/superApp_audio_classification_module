"""Hardening contracts without an internet connection or model download."""
import hashlib
import io
from pathlib import Path
import pytest
from app.core.config import MODELS, Settings
from app.core.model_integrity import verify_model
from app.inference.classifier import UPSTREAM
from app.audio.validation import AudioTooLarge, check_upload


def test_vendored_model_sources_present():
    assert (UPSTREAM / "models/mn/model.py").is_file()
    assert (UPSTREAM / "models/preprocess.py").is_file()
    assert (UPSTREAM / "metadata/class_labels_indices.csv").is_file()


def test_production_fails_closed_without_digest():
    with pytest.raises(ValueError, match="EXPECTED_MODEL_SHA256"):
        Settings(app_env="production", api_token="a" * 32)
    with pytest.raises(ValueError, match="hexadecimal"):
        Settings(app_env="test", expected_model_sha256="invalid")
    with pytest.raises(ValueError, match="token|Token|REPLACE"):
        Settings(app_env="production", api_token="REPLACE_" + "x" * 32,
                 expected_model_sha256="a" * 64)


def test_oversized_upload_has_distinct_error():
    with pytest.raises(AudioTooLarge):
        check_upload(b"x" * 1001, "audio.wav", 1000)


def test_download_once_then_reuse_cached_volume(monkeypatch, tmp_path):
    from scripts import prepare_model
    payload = b"small synthetic checkpoint fixture"
    digest = hashlib.sha256(payload).hexdigest()
    monkeypatch.setitem(MODELS, "mn10_as", {**MODELS["mn10_as"], "size": len(payload)})
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_TOKEN", "a" * 32)
    monkeypatch.setenv("MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("MODEL_NAME", "mn10_as")
    monkeypatch.setenv("EXPECTED_MODEL_SHA256", digest)

    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *_): self.close()
    calls = []
    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return Response(payload)
    monkeypatch.setattr(prepare_model.urllib.request, "urlopen", fake_urlopen)
    prepare_model.main()
    prepare_model.main()
    assert len(calls) == 1
    settings = Settings()
    assert verify_model(settings)["sha256"] == digest

    (tmp_path / settings.model_spec["filename"]).write_bytes(b"altered")
    with pytest.raises(RuntimeError):
        prepare_model.main()


def test_production_digest_checked_even_if_manifest_matches_local_file(monkeypatch,tmp_path):
    from scripts import prepare_model
    payload = b"fixture"
    digest = hashlib.sha256(payload).hexdigest()
    monkeypatch.setitem(MODELS,"mn10_as",{**MODELS["mn10_as"],"size":len(payload)})
    monkeypatch.setenv("APP_ENV","development")
    monkeypatch.setenv("MODEL_DIR",str(tmp_path))
    monkeypatch.setenv("EXPECTED_MODEL_SHA256",digest)
    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self,*_): self.close()
    monkeypatch.setattr(prepare_model.urllib.request,"urlopen",lambda *_args,**_kwargs:Response(payload))
    prepare_model.main()
    monkeypatch.setenv("EXPECTED_MODEL_SHA256","0"*64)
    with pytest.raises(RuntimeError,match="pinned"):
        verify_model(Settings())


def test_model_setup_production_no_api_secret(monkeypatch,tmp_path):
    from app.core.config import ModelSetupSettings
    monkeypatch.setenv("APP_ENV","production")
    monkeypatch.setenv("API_TOKEN","")
    monkeypatch.setenv("EXPECTED_MODEL_SHA256","a"*64)
    monkeypatch.setenv("MODEL_DIR",str(tmp_path))
    setup = ModelSetupSettings()
    assert setup.model_name == "mn10_as"
    assert setup.model_dir == tmp_path
    with pytest.raises(ValueError,match="token"):
        Settings()


def test_model_setup_rejects_missing_prod_digest(monkeypatch):
    from app.core.config import ModelSetupSettings
    monkeypatch.setenv("APP_ENV","production")
    monkeypatch.delenv("EXPECTED_MODEL_SHA256",raising=False)
    with pytest.raises(ValueError,match="EXPECTED_MODEL_SHA256"):
        ModelSetupSettings()
