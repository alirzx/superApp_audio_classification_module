from pathlib import Path

class InvalidAudio(ValueError): pass
class AudioTooLarge(InvalidAudio): pass

ALLOWED_SUFFIXES={".wav",".mp3",".flac",".ogg",".m4a",".aac",".webm"}

def check_upload(data: bytes, filename: str, max_bytes: int):
    if not data: raise InvalidAudio("Empty audio")
    if len(data)>max_bytes: raise AudioTooLarge("Audio too large")
    if Path(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise InvalidAudio("Unsupported audio extension")
