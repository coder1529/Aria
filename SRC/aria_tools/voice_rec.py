import re
import torch
from transformers import pipeline
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000

HALLUCINATIONS = ["subtitles by", "thank you for watching", "amara.org",
                  "시청해주셔서 감사합니다", "구독과 좋아요"]

def record(seconds):
    print("Recording...")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()                     # block until recording finishes
    print("Done.")
    return audio.flatten()        # (N, 1) -> (N,)

asr = pipeline(
    "automatic-speech-recognition",
    model="models/whisper-large-v3-turbo",
    dtype=torch.float16,
    device="cuda",
)

def transcribe(audio):
    result = asr({"raw": audio, "sampling_rate": SAMPLE_RATE}, generate_kwargs={"language": "en"})
    text = result["text"].strip()
    words = text.lower().split()
    if re.search(r"[\u0400-\u04FF]", text):     # Cyrillic letters
        return ""
    if any(h in text.lower() for h in HALLUCINATIONS):
        return ""
    if len(words) > 8 and len(set(words)) / len(words) < 0.3:
        return ""
    return text

def record_until_silence(threshold=0.01, silence_seconds=1.0, max_seconds=15):
    chunk_size = int(0.1 * SAMPLE_RATE)        # 0.1 s per chunk
    chunks = []
    started = False                            # has the user started talking?
    quiet_chunks = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        print("Listening...")
        while len(chunks) * 0.1 < max_seconds:
            chunk, _ = stream.read(chunk_size)
            chunk = chunk.flatten()
            chunks.append(chunk)
            rms = np.sqrt(np.mean(chunk ** 2))

            if rms > threshold:
                started = True
                quiet_chunks = 0          # talking again, reset the counter
            elif started:
                quiet_chunks += 1
                if quiet_chunks * 0.1 >= silence_seconds:
                    break
    print("Done.")
    return np.concatenate(chunks)

if __name__ == "__main__":
    audio = record_until_silence()
    print(len(audio) / SAMPLE_RATE, "seconds")
    print(transcribe(audio))