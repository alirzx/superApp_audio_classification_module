import numpy as np
from .decoder import SAMPLE_RATE

def segment_audio(audio: np.ndarray, window_seconds: int):
    size=window_seconds*SAMPLE_RATE
    for start in range(0,len(audio),size):
        piece=audio[start:start+size]
        if not len(piece): continue
        padded=np.pad(piece,(0,size-len(piece))) if len(piece)<size else piece
        yield start/SAMPLE_RATE,(start+len(piece))/SAMPLE_RATE,padded.astype("float32",copy=False)
