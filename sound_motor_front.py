import sounddevice as sd
import numpy as np
import asyncio
import websockets
import json
import threading
import time

# =========================
# AUDIO CONFIG
# =========================
INPUT_DEVICE_INDEX = 2   # USB Audio Device (1 in, 2 out)
SAMPLE_RATE = 44100
RECORD_SECONDS = 4

sd.default.device = (INPUT_DEVICE_INDEX, None)
sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1

# =========================
# WEBSOCKET UI SERVER
# =========================
connected_clients = set()

async def ws_handler(websocket):
    connected_clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    finally:
        connected_clients.remove(websocket)

async def send_to_ui(payload):
    if connected_clients:
        msg = json.dumps(payload)
        await asyncio.gather(
            *[client.send(msg) for client in connected_clients],
            return_exceptions=True
        )

async def websocket_server():
    async with websockets.serve(ws_handler, "0.0.0.0", 8765):
        print("🟢 WebSocket UI connected on ws://localhost:8765")
        await asyncio.Future()

def start_websocket():
    asyncio.run(websocket_server())

# Start WS server in background
threading.Thread(target=start_websocket, daemon=True).start()

# =========================
# AUDIO RECORDING
# =========================
def record_audio(seconds):
    print("🎙 Recording...")
    audio = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    return audio.flatten()

# =========================
# EMOTION LOGIC (stub)
# =========================
def determine_emotion(text):
    text = text.lower()
    if "hate" in text or "angry" in text:
        return "angry"
    if "love" in text or "cute" in text:
        return "happy"
    return "responding"

# =========================
# MAIN CAT LOOP
# =========================
print("\n🐱 Cat AI Ready. Press Enter to talk.\n")

while True:
    input("Press Enter to speak...")

    audio = record_audio(RECORD_SECONDS)

    # ---- YOUR EXISTING LOGIC GOES HERE ----
    # speech_to_text(audio)
    # response = chatgpt(...)
    # elevenlabs_tts(response)
    # motor_control(emotion)

    response = "Wow. You really just said that."
    emotion = determine_emotion(response)

    asyncio.run(send_to_ui({
        "mood": emotion,
        "response": response,
        "typing": True,
        "typing_speed": 55
    }))

    time.sleep(2)

    asyncio.run(send_to_ui({
        "mood": "idle"
    }))
