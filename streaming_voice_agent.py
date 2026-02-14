import os
import json
import requests
import sounddevice as sd
import soundfile as sf
import numpy as np
from io import BytesIO

API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise ValueError("Set ELEVENLABS_API_KEY")

AGENT_ID = "agent_5301khev8757e4qskqcpqhq6em2e"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"   # replace if desired

# -------------------------
# auto select duplex device
# -------------------------
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        sd.default.device = (i, i)
        print("Using device:", d["name"])
        break

# -------------------------
# helper: TTS + play
# -------------------------
def speak(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }

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

# -------------------------
# SIMULATE CONVERSATION (stable endpoint)
# -------------------------
url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation"

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "simulation_specification": {
        "simulated_user_config": {
            "first_message": "Hello there!",
            "language": "en"
        }
    },
    "new_turns_limit": 1
}


print("\nRunning conversation simulation...\n")

r = requests.post(url, headers=headers, json=payload)

if r.status_code != 200:
    print(r.text)
    raise RuntimeError("Simulation failed")

data = r.json()

turns = data.get("simulated_conversation", [])

for turn in turns:
    role = turn.get("role", "agent")
    text = turn.get("message", "")

    if not text:
        continue

    print(f"{role.upper()}: {text}")

    if role == "agent":
        speak(text)

print("\nSimulation finished.")
