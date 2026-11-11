import subprocess
import numpy as np
from .validation import InvalidAudio

SAMPLE_RATE=32000

def decode_audio(data: bytes, *, max_duration: int, max_decode_bytes: int) -> np.ndarray:
    cmd=["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-threads","1",
         "-i","pipe:0","-map","0:a:0","-vn","-ac","1","-ar",str(SAMPLE_RATE),
         "-t",str(max_duration+1),"-f","f32le","pipe:1"]
    try:
        proc=subprocess.run(cmd,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                            timeout=min(120,max(15,max_duration*2)),check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise InvalidAudio("Audio decoding failed or timed out") from exc
    if proc.returncode or not proc.stdout or len(proc.stdout)%4: raise InvalidAudio("Invalid or undecodable audio")
    if len(proc.stdout)>max_decode_bytes: raise InvalidAudio("Decoded audio too large")
    pcm=np.frombuffer(proc.stdout,dtype="<f4").copy()
    if not np.all(np.isfinite(pcm)): raise InvalidAudio("Nonfinite audio")
    duration=len(pcm)/SAMPLE_RATE
    if duration>max_duration+1/SAMPLE_RATE: raise InvalidAudio("Audio exceeds maximum duration")
    if duration<.25: raise InvalidAudio("Audio shorter than 0.25s")
    return pcm
