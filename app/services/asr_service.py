from functools import lru_cache
from transformers import pipeline

@lru_cache(maxsize=1)
def get_asr_model():
    return pipeline("automatic-speech-recognition", model="openai/whisper-small")


def transcribe_audio(filepath: str) -> str:
    model = get_asr_model()
    result = model(filepath)
    return result[model]