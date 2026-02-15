import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
from io import BytesIO
import random
import glob
import time
from motors_just_fcns import motorA_forward, motorB_forward, stop_motors, cleanup_motors

import asyncio
import websockets
import json
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer

# ---------------------------- CONFIG ----------------------------
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise ValueError("Set ELEVENLABS_API_KEY environment variable!")

AGENT_ID = "agent_1601khf3r1jfff2saez29f6frfny"  # your agent ID
VOICE_ID = "XdflFrQO8wbGpWMNZHFr"                 # your TTS voice ID

RECORD_SECONDS = 5
CAT_SOUNDS_FOLDER = "cat_sounds"
WS_PORT = 8765
HTTP_PORT = 8000

connected_clients = set()

# ---------------------------- AUDIO DEVICE ----------------------------
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        sd.default.device = (i, i)
        print("Using audio device:", d["name"])
        DEFAULT_SR = int(d['default_samplerate'])
        break
else:
    raise RuntimeError("No suitable input/output device found")

# ---------------------------- AUDIO HELPERS ----------------------------
def resample_audio(audio, orig_sr, target_sr):
    if orig_sr == target_sr:
        return audio.astype(np.float32)
    duration = len(audio) / orig_sr
    new_length = int(duration * target_sr)
    if audio.ndim == 1:
        resampled = np.interp(np.linspace(0, len(audio)-1, new_length), np.arange(len(audio)), audio)
    else:
        channels = [np.interp(np.linspace(0, len(audio)-1, new_length), np.arange(len(audio)), audio[:, ch])
                    for ch in range(audio.shape[1])]
        resampled = np.stack(channels, axis=1)
    return resampled.astype(np.float32)

def record_audio(seconds, samplerate):
    print(f"Recording for {seconds} seconds at {samplerate} Hz...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

def speech_to_text(audio_np, samplerate):
    wav_file = "temp.wav"
    sf.write(wav_file, audio_np, samplerate)
    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": API_KEY}
    files = {"file": ("temp.wav", open(wav_file, "rb"), "audio/wav")}
    data = {"model_id": "scribe_v2"}
    r = requests.post(url, headers=headers, files=files, data=data)
    if r.status_code != 200:
        print("STT failed:", r.text)
        return ""
    return r.json().get("text", "")

def play_audio(audio_data, sr):
    audio_data = resample_audio(audio_data, sr, DEFAULT_SR)
    audio_data = audio_data.astype(np.float32)
    audio_data = audio_data / np.max(np.abs(audio_data))
    sd.play(audio_data, DEFAULT_SR)
    sd.wait()

def play_audio_dont_wait(audio_data, sr):
    audio_data = resample_audio(audio_data, sr, DEFAULT_SR)
    audio_data = audio_data.astype(np.float32)
    audio_data = audio_data / np.max(np.abs(audio_data))
    sd.play(audio_data, DEFAULT_SR)

def get_speech_from_elevenlabs(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_monolingual_v1"}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("TTS failed:", r.text)
        return None, None
    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    return data, sr

def get_amplitude_envelope(data, sr, fps=30):
    chunk_size = sr // fps
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
    num_chunks = len(data) // chunk_size
    truncated_data = data[:num_chunks * chunk_size]
    chunks = truncated_data.reshape(num_chunks, chunk_size)
    rms_values = np.sqrt(np.mean(chunks**2, axis=1))
    max_rms = np.max(rms_values)
    return rms_values / max_rms if max_rms > 0 else rms_values

def play_cat_sound():
    cat_files = glob.glob(os.path.join(CAT_SOUNDS_FOLDER, "*.wav"))
    if not cat_files:
        return
    cat_file = random.choice(cat_files)
    data, sr = sf.read(cat_file, dtype="float32")
    play_audio(data, sr)

def play_cat_sound_and_move_motor(data, sr):
    play_cat_sound()
    amplitudes = get_amplitude_envelope(data, sr, fps=30)
    delay_between_frames = 1.0 / 30
    play_audio_dont_wait(data, sr)
    for amp in amplitudes:
        start_time = time.time()
        if amp > 0.1:
            speed = int(amp * 100)
            motorA_forward(speed=speed)
            motorB_forward(speed=speed)
        else:
            stop_motors()
        elapsed = time.time() - start_time
        time.sleep(max(0, delay_between_frames - elapsed))
    stop_motors()
    sd.wait()
    play_cat_sound()

def agent_reply(user_text):
    url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "simulation_specification": {
            "simulated_user_config": {"first_message": user_text, "language": "en"},
            "agent_config": {"persona": "You are a toxic cat assistant...", "llm_override": "Respond in toxic cat style"}
        },
        "new_turns_limit": 1
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("Agent call failed:", r.text)
        return ""
    turns = r.json().get("simulated_conversation", [])
    for turn in turns:
        if turn.get("role") == "agent":
            return turn.get("message", "").replace("[sarcastic]", "").strip()
    return ""

# ---------------------------- WEBSOCKET ----------------------------
async def ws_handler(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def send_ui_update(data):
    if connected_clients:
        msg = json.dumps(data)
        await asyncio.gather(*(ws.send(msg) for ws in connected_clients))

# ---------------------------- VOICE LOOP ----------------------------
async def voice_loop():
    print("\nVoice agent ready! Speak into your mic.\n")
    try:
        while True:
            input("Press Enter to record your message...")
            await send_ui_update({"mood": "responding", "clear_response": True})
            audio_np = record_audio(RECORD_SECONDS, DEFAULT_SR)
            user_text = speech_to_text(audio_np, DEFAULT_SR)
            if not user_text:
                continue
            reply_text = agent_reply(user_text)
            if not reply_text:
                continue
            await send_ui_update({"response": reply_text, "typing": True, "typing_speed": 40})
            data, sr = get_speech_from_elevenlabs(reply_text)
            if data is not None:
                play_cat_sound_and_move_motor(data, sr)
            await send_ui_update({"mood": "idle"})
    except KeyboardInterrupt:
        cleanup_motors()

# ---------------------------- HTTP SERVER ----------------------------
def start_http_server():
    server = HTTPServer(("0.0.0.0", HTTP_PORT), SimpleHTTPRequestHandler)
    print(f"🌐 UI → http://localhost:{HTTP_PORT}")
    server.serve_forever()

# ---------------------------- MAIN ----------------------------
async def main():
    # Run HTTP server in separate thread
    Thread(target=start_http_server, daemon=True).start()

    # Start WebSocket server
    await websockets.serve(ws_handler, "0.0.0.0", WS_PORT)
    print(f"🌐 WebSocket server running on ws://localhost:{WS_PORT}")

    # Start voice loop
    await voice_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Exiting and cleaning up motors...")
        cleanup_motors()
