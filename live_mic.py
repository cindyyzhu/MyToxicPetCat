import os
import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
from io import BytesIO

# -----------------------
# CONFIG
# -----------------------
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise RuntimeError("Please set ELEVENLABS_API_KEY")

AGENT_ID = "agent_5301khev8757e4qskqcpqhq6em2e"  # your agent
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"                 # your real voice_id

RECORD_SECONDS = 5  # seconds to record per turn

# -----------------------
# Auto-select USB mic + speaker
# -----------------------
devices = sd.query_devices()
usb_index = None
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0 and d['max_output_channels'] > 0 and "USB" in d['name']:
        usb_index = i
        break
if usb_index is None:
    raise RuntimeError("No USB duplex device found")

sd.default.device = (usb_index, usb_index)
print("Using audio device:", devices[usb_index]['name'])

# -----------------------
# Helper: record audio from mic
# -----------------------
def record_audio(seconds=RECORD_SECONDS):
    device_info = sd.query_devices(sd.default.device[0])
    samplerate = int(device_info['default_samplerate'])
    print(f"Recording for {seconds} seconds at {samplerate} Hz...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten(), samplerate

# -----------------------
# Helper: TTS and play
# -----------------------
def speak(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_monolingual_v1"}

    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("TTS failed:", r.text)
        return

    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    sd.play(data, sr)
    sd.wait()

# -----------------------
# Helper: STT (Scribe v2)
# -----------------------
def speech_to_text(audio_np, samplerate):
    url = "https://api.elevenlabs.io/v1/speech-to-text"
    files = {
        "file": ("audio.wav", sf.write("temp.wav", audio_np, samplerate), "audio/wav")
    }
    # Actually simplest: write temp file
    wav_file = "temp.wav"
    sf.write(wav_file, audio_np, samplerate)

    headers = {"xi-api-key": API_KEY}
    with open(wav_file, "rb") as f:
        r = requests.post(url, headers=headers, files={"file": f})
    if r.status_code != 200:
        print("STT failed:", r.text)
        return ""
    result = r.json()
    return result.get("text", "")

# -----------------------
# Helper: send text to agent
# -----------------------
def agent_reply(text):
    url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "simulation_specification": {
            "simulated_user_config": {"first_message": text, "language": "en"}
        },
        "new_turns_limit": 1
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("Agent call failed:", r.text)
        return ""
    data = r.json()
    turns = data.get("simulated_conversation", [])
    if not turns:
        return ""
    # return agent's first reply
    for turn in turns:
        if turn.get("role") == "agent":
            return turn.get("message", "")
    return ""

# -----------------------
# Main loop
# -----------------------
print("\nVoice agent ready! Speak into your USB mic.")

while True:
    input("Press Enter to record your message...")
    audio_np, sr = record_audio()
    user_text = speech_to_text(audio_np, sr)
    if not user_text:
        print("No speech detected.")
        continue
    print("YOU:", user_text)

    reply_text = agent_reply(user_text)
    if not reply_text:
        print("Agent did not reply.")
        continue

    print("AGENT:", reply_text)
    speak(reply_text)
