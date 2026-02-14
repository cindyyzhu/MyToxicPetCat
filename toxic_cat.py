import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
from io import BytesIO

# ----------------------------
# CONFIG
# ----------------------------
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise ValueError("Set ELEVENLABS_API_KEY environment variable!")

AGENT_ID = "agent_5301khev8757e4qskqcpqhq6em2e"  # your agent ID
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"                  # your TTS voice ID

RECORD_SECONDS = 5

# ----------------------------
# auto-select duplex audio device
# ----------------------------
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        sd.default.device = (i, i)
        print("Using audio device:", d["name"])
        DEFAULT_SR = int(d['default_samplerate'])
        break
else:
    raise RuntimeError("No suitable input/output device found")

# ----------------------------
# HELPER: Record from mic
# ----------------------------
def record_audio(seconds, samplerate):
    print(f"Recording for {seconds} seconds at {samplerate} Hz...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

# ----------------------------
# HELPER: Speech-to-text using Scribe v2
# ----------------------------
def speech_to_text(audio_np, samplerate):
    wav_file = "temp.wav"
    sf.write(wav_file, audio_np, samplerate)

    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": API_KEY}
    files = {"file": ("temp.wav", open(wav_file, "rb"), "audio/wav")}
    data = {"model_id": "scribe_v2"}  # correct model for Scribe v2

    r = requests.post(url, headers=headers, files=files, data=data)
    if r.status_code != 200:
        print("STT failed:", r.text)
        return ""
    result = r.json()
    return result.get("text", "")

# ----------------------------
# HELPER: TTS and playback
# ----------------------------
def speak(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1"
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("TTS failed:", r.text)
        return
    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    sd.play(data, sr)
    sd.wait()

# ----------------------------
# HELPER: Get agent response
# ----------------------------
def agent_reply(user_text):
    url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "simulation_specification": {
            "simulated_user_config": {
                "first_message": user_text,
                "language": "en"
            },
            "agent_config": {
                "persona": (
                    "You are a cat-like AI assistant. You are clever, sassy, and slightly toxic. "
                    "You think you are smarter than humans and sometimes mock them, "
                    "but you respond in a playful, cat-like tone."
                )
            }
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
    for turn in turns:
        if turn.get("role") == "agent":
            return turn.get("message", "")
    return ""

# ----------------------------
# MAIN LOOP
# ----------------------------
print("\nVoice agent ready! Speak into your mic.")
print("Press Enter to start recording a message, Ctrl+C to exit.\n")

try:
    while True:
        input("Press Enter to record your message...")
        audio_np = record_audio(RECORD_SECONDS, DEFAULT_SR)
        print("Processing...")
        user_text = speech_to_text(audio_np, DEFAULT_SR)
        if not user_text:
            print("No speech detected.\n")
            continue

        print(f"\nYOU: {user_text}")
        reply_text = agent_reply(user_text)
        if not reply_text:
            print("Agent did not respond.\n")
            continue

        print(f"CAT AI: {reply_text}\n")
        speak(reply_text)

except KeyboardInterrupt:
    print("\nExiting. Bye!")
