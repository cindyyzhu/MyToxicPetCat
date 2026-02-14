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
# STREAM SIMULATION
# -------------------------
url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation/stream"

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
    }
}

print("\nStarting streaming simulation...\n")

with requests.post(url, headers=headers, json=payload, stream=True) as r:

    if r.status_code != 200:
        print(r.text)
        raise RuntimeError("Stream failed")

    buffer = ""

    for chunk in r.iter_content(chunk_size=None):
        if not chunk:
            continue

        buffer += chunk.decode("utf-8")

        # server-sent-events style lines
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)

            if not line.strip():
                continue

            try:
                event = json.loads(line)
            except:
                continue

            if "message" in event:
                role = event.get("role", "agent")
                text = event["message"]

                print(f"{role.upper()}: {text}")

                if role == "agent":
                    speak(text)

print("\nSimulation finished.")
