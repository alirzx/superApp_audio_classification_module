from pathlib import Path
import sys
import numpy as np
from app.core.config import Settings
from app.core.model_integrity import verify_model

UPSTREAM=Path(__file__).resolve().parents[3]/"third_party"/"efficientat"

class EfficientATClassifier:
    def __init__(self, settings: Settings):
        self.settings=settings
        self.model=None
        self.mel=None
        self.labels=[]
        self.ready=False

    def initialize(self):
        verify_model(self.settings)
        if str(UPSTREAM) not in sys.path: sys.path.insert(0,str(UPSTREAM))
        import torch
        from models.mn.model import get_model
        from models.preprocess import AugmentMelSTFT
        from helpers.utils import labels
        torch.set_num_threads(self.settings.cpu_threads)
        if torch.version.cuda is not None: raise RuntimeError("CPU-only PyTorch required")
        model=get_model(pretrained_name=None,width_mult=self.settings.model_spec["width"],num_classes=527)
        state=torch.load(self.settings.checkpoint,map_location="cpu",weights_only=True)
        if isinstance(state,dict) and "state_dict" in state: state=state["state_dict"]
        model.load_state_dict(state,strict=True)
        self.model=model.cpu().eval()
        self.mel=AugmentMelSTFT(n_mels=128,sr=32000,win_length=800,hopsize=320,
                                 freqm=0,timem=0).cpu().eval()
        self.labels=list(labels)
        if len(self.labels)!=527: raise RuntimeError("Expected 527 AudioSet labels")
        self.ready=True

    def predict(self, samples: np.ndarray) -> list[float]:
        if not self.ready: raise RuntimeError("Model unavailable")
        import torch
        with torch.inference_mode():
            waveform=torch.from_numpy(np.ascontiguousarray(samples,dtype=np.float32)).unsqueeze(0)
            spec=self.mel(waveform)
            logits,_=self.model(spec.unsqueeze(0))
            scores=torch.sigmoid(logits.float()).reshape(-1)
        if scores.numel()!=527 or not torch.isfinite(scores).all():
            raise RuntimeError("Malformed model output")
        return scores.cpu().tolist()
