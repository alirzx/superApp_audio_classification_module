from typing import Protocol
import numpy as np

class Classifier(Protocol):
    ready: bool
    labels: list[str]
    def initialize(self) -> None: ...
    def predict(self,samples: np.ndarray) -> list[float]: ...
