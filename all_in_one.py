#!/usr/bin/env python3
import os
import asyncio
import json
import time
import random
import glob
from io import BytesIO
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
import websockets

from motors_just_fcns import (
    motorA_forward,
    motorB_forward,
    stop_motors,
    cleanup_motors
)

# ============================ CONFIG ============================

API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise RuntimeError("Set ELEVENLABS_API_KEY")

AGENT_ID = "agent_1601khf3r1jfff2saez29f6frfny"
VOICE_ID = "XdflFrQO8wbGpWMNZHFr"

RECORD_SECONDS = 5
CAT_SOUNDS_FOLDER = "cat_sounds"

HTTP_PORT = 8000
WS_PORT = 8765

connected_clients = set()

# ============================ AUDIO DEVICE ============================

sd.default.device = (2, 2)  # USB Audio Device (1 in, 2 out)
DEFAULT_SR = int(sd.query_devices(2)["default_samplerate"])

# ============================ HTML ============================

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>My Toxic Pet Cat</title>
<style>
body { background:#120820; color:#eee; font-family: monospace; }
#speech { border:2px solid #0ff; padding:20px; height:150px; }
</style>
</head>
<body>
<h1>😾 My Toxic Pet Cat</h1>
<div id="speech"></div>
<p id="mood">Mood: idle</p>

<script>
const ws = new WebSocket("ws://localhost:8765");

ws.onmessage = e => {
  const d = JSON.parse(e.data);
  if (d.mood) document.getElementById("mood").innerText = "Mood: " + d.mood;
  if (d.clear_response) document.getElementById("speech").innerText = "";
  if (d.response) {
    let i = 0;
    document.getElementById("speech").innerText = "";
    const t = setInterval(() => {
      document.getElementById("speech").innerText += d.response[i++];
      if (i >= d.response.length) clearInterval(t);
    }, d.typing_speed || 40);
  }
};
</script>
</body>
</html>
"""

# ============================ HTTP SERVER ============================

class FrontendHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode())

def start_http():
    server = HTTPServer(("0.0.0.0", HTTP_PORT), FrontendHandler)
    print(f"🌐 UI → http://localhost:{HTTP_PORT}")
    server.serve_forever()

# ============================ WEBSOCKET ============================

async def ws_handler(ws):
    connected_clients.add(ws)
    try:
        await ws.wait_closed()
    finally:
        connected_clients.remove(ws)

async def ui(data):
    if connected_clients:
        msg = json.dumps(data)
        await asyncio.gather(*(c.send(msg) for c in connected_clients))

# ============================ AUDIO HELPERS ============================

def record_audio():
    audio = sd.rec(int(RECORD_SECONDS * DEFAULT_SR),
                   samplerate=DEFAULT_SR,
                   channels=1,
                   dtype="float32")
    sd.wait()
    return audio.flatten()

def stt(audio):
    sf.write("tmp.wav", audio, DEFAULT_SR)
    r = requests.post(
        "https://api.elevenlabs.io/v1/speech-to-text",
        headers={"xi-api-key": API_KEY},
        files={"file": open("tmp.wav","rb")},
        data={"model_id":"scribe_v2"}
    )
    return r.json().get("text","") if r.ok else ""

def tts(text):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={"xi-api-key":API_KEY,"Content-Type":"application/json"},
        json={"text":text,"model_id":"eleven_monolingual_v1"}
    )
    return sf.read(BytesIO(r.content), dtype="float32")

def play_and_move(data, sr):
    sd.play(data, sr, blocking=False)
    amps = np.abs(data.mean(axis=1) if data.ndim > 1 else data)
    amps /= np.max(amps)

    for a in amps[::sr//30]:
        if a > 0.1:
            speed = int(40 + a * 60)
            motorA_forward(speed)
            motorB_forward(speed)
        else:
            stop_motors()
        time.sleep(1/30)

    stop_motors()
    sd.wait()

# ============================ AGENT ============================

def agent_reply(text):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation",
        headers={"xi-api-key":API_KEY,"Content-Type":"application/json"},
        json={
            "simulation_specification":{
                "simulated_user_config":{"first_message":text},
                "agent_config":{"llm_override":"toxic cat"}
            },
            "new_turns_limit":1
        }
    )
    for t in r.json().get("simulated_conversation",[]):
        if t["role"]=="agent":
            return t["message"]
    return ""

# ============================ MAIN LOOP ============================

async def voice_loop():
    print("🎙️ Press Enter to talk")
    while True:
        input()
        await ui({"mood":"responding","clear_response":True})

        audio = record_audio()
        text = stt(audio)
        if not text:
            await ui({"mood":"idle"})
            continue

        reply = agent_reply(text)
        await ui({"response":reply,"typing":True,"typing_speed":35})

        data, sr = tts(reply)
        play_and_move(data, sr)

        await ui({"mood":"idle"})

# ============================ START ============================

if __name__ == "__main__":
    threading.Thread(target=start_http, daemon=True).start()
    asyncio.run(websockets.serve(ws_handler, "0.0.0.0", WS_PORT))
    asyncio.run(voice_loop())
