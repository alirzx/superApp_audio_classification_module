from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MODELS = {
    "mn10_as": {"filename": "mn10_as_mAP_471.pt", "size": 19708753, "width": 1.0, "map": .471},
    "mn04_as": {"filename": "mn04_as_mAP_432.pt", "size": 4066513, "width": .4, "map": .432},
}
RELEASE = "v0.0.1"
RELEASE_BASE = "https://github.com/fschmid56/EfficientAT/releases/download/v0.0.1/"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    app_env: str = "development"
    api_token: str = ""
    model_name: str = "mn10_as"
    model_dir: Path = Path("/models")
    cpu_threads: int = Field(2, ge=1, le=32)
    max_concurrent_inference: int = Field(1, ge=1, le=4)
    max_queue_wait_seconds: float = Field(10, gt=0, le=120)
    max_upload_mb: int = Field(20, ge=1, le=100)
    max_request_bytes: int = Field(22*1024*1024, gt=0)
    max_duration_seconds: int = Field(60, ge=5, le=600)
    max_decode_bytes: int = Field(80*1024*1024, ge=1024*1024)
    window_seconds: int = Field(10, ge=2, le=30)
    top_k: int = Field(10, ge=1, le=50)
    score_threshold: float = Field(.10, ge=0, le=1)
    enable_metrics: bool = True

    @model_validator(mode="after")
    def validate_settings(self):
        if self.model_name not in MODELS: raise ValueError("Unsupported model")
        if self.app_env not in {"test","development","production"}: raise ValueError("Invalid APP_ENV")
        if self.app_env == "production" and len(self.api_token) < 24: raise ValueError("Production token must be >=24 chars")
        if self.max_request_bytes <= self.max_upload_mb*1024*1024: raise ValueError("Request limit must exceed upload limit")
        if self.window_seconds > self.max_duration_seconds: raise ValueError("Window too long")
        if self.max_decode_bytes < self.max_duration_seconds*32000*4: raise ValueError("Decode limit too small")
        return self

    @property
    def model_spec(self): return MODELS[self.model_name]
    @property
    def checkpoint(self): return self.model_dir / self.model_spec["filename"]
    @property
    def manifest(self): return self.model_dir / (self.model_name+".manifest.json")
