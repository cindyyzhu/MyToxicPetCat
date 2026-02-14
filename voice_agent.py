import os
import json
import requests
import numpy as np
import sounddevice as sd
import soundfile as sf
import resampy

# ----------------------------
# CONFIG
# ----------------------------
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise ValueError("Set ELEVENLABS_API_KEY first")

RECORD_SECONDS = 4
TARGET_SR = 16000

# 🔹 put your real voice_id here (NOT name)
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"   # default demo voice
MODEL_ID = "eleven_monolingual_v1"

# ----------------------------
# AUTO DEVICE DETECT
# ----------------------------
devices = sd.query_devices()
device_index = None

for i, d in enumerate(devices):
    if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        device_index = i
        break

if device_index is None:
    raise RuntimeError("No full-duplex device found")

sd.default.device = (device_index, device_index)
info = sd.query_devices(device_index)

mic_sr = int(info["default_samplerate"])
print("Using device:", info["name"])
print("Mic SR:", mic_sr)

# ----------------------------
# RECORD
# ----------------------------
print("Speak now...")
audio = sd.rec(int(RECORD_SECONDS * mic_sr),
               samplerate=mic_sr,
               channels=1,
               dtype="float32")
sd.wait()
audio = audio.flatten()

# resample if needed
if mic_sr != TARGET_SR:
    audio = resampy.resample(audio, mic_sr, TARGET_SR)

sf.write("mic.wav", audio, TARGET_SR)
print("Saved mic.wav")

# ----------------------------
# ELEVENLABS TTS (DOC METHOD)
# ----------------------------
text = "Hello Cindy, your voice agent is working."

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "text": text,
    "model_id": MODEL_ID,
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.8
    }
}

print("Requesting ElevenLabs TTS...")

r = requests.post(url, headers=headers, json=payload)

if r.status_code != 200:
    print(r.text)
    raise RuntimeError("TTS request failed")

with open("tts.wav", "wb") as f:
    f.write(r.content)

print("Saved tts.wav")

# ----------------------------
# PLAYBACK
# ----------------------------
data, sr = sf.read("tts.wav", dtype="float32")
sd.play(data, sr)
sd.wait()

print("Done!")
