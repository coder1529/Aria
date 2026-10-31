# import re
# import time
# import pyttsx3

# ENGLISH_VOICE = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"

# def speak(text):
#     engine = pyttsx3.init()
#     engine.setProperty("voice", ENGLISH_VOICE)
#     engine.say('<silence msec="500"/>' + text)
#     engine.runAndWait()
#     engine.stop()

import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro

MODEL_DIR = "models/kokoro"
VOICE = "af_heart"          # American female; try "af_bella", "af_sarah", or "bf_emma" (British)

kokoro = Kokoro(f"{MODEL_DIR}/kokoro-v1.0.onnx", f"{MODEL_DIR}/voices-v1.0.bin")

def speak(text):
    samples, sample_rate = kokoro.create(text, voice=VOICE, speed=1.0, lang="en-us")
    silence = np.zeros(int(0.3 * sample_rate))       # 0.3 seconds of quiet up front
    audio = np.concatenate([silence, samples])
    sd.play(audio, sample_rate)
    sd.wait()                                  # block until she finishes talking