import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
from io import BytesIO
import random
import glob

# ---------------------------- CONFIG ----------------------------
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise ValueError("Set ELEVENLABS_API_KEY environment variable!")

AGENT_ID = "agent_1601khf3r1jfff2saez29f6frfny"
VOICE_ID = "XdflFrQO8wbGpWMNZHFr"
RECORD_SECONDS = 5
CAT_SOUNDS_FOLDER = "cat_sounds"

# ---------------------------- DEVICE SELECTION ----------------------------
print("Available audio devices:")
for i, d in enumerate(sd.query_devices()):
    print(i, d["name"], "| IN:", d["max_input_channels"], "OUT:", d["max_output_channels"])

# Select first USB full-duplex device
device_index = None
for i, d in enumerate(sd.query_devices()):
    if "USB" in d["name"] and d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        device_index = i
        break

if device_index is None:
    # fallback to first full-duplex device
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
            device_index = i
            break

if device_index is None:
    raise RuntimeError("No suitable input/output device found")

sd.default.device = (device_index, device_index)
DEFAULT_SR = int(sd.query_devices(device_index)["default_samplerate"])
print("Using audio device:", sd.query_devices(device_index)["name"])
print("Device SR:", DEFAULT_SR)

# ---------------------------- HELPERS ----------------------------
def resample_audio(audio, orig_sr, target_sr):
    if orig_sr == target_sr:
        return audio.astype(np.float32)
    duration = len(audio) / orig_sr
    new_length = int(duration * target_sr)
    if audio.ndim == 1:
        resampled = np.interp(
            np.linspace(0, len(audio)-1, new_length),
            np.arange(len(audio)),
            audio
        )
    else:
        channels = []
        for ch in range(audio.shape[1]):
            channels.append(
                np.interp(
                    np.linspace(0, len(audio)-1, new_length),
                    np.arange(len(audio)),
                    audio[:, ch]
                )
            )
        resampled = np.stack(channels, axis=1)
    return resampled.astype(np.float32)

def record_audio(seconds, samplerate):
    print(f"Recording {seconds}s at {samplerate} Hz...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

def play_audio(audio_data, sr):
    audio_data = resample_audio(audio_data, sr, DEFAULT_SR)
    audio_data = audio_data.astype(np.float32)
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val
    sd.play(audio_data, DEFAULT_SR)
    sd.wait()

def play_cat_sound():
    cat_files = glob.glob(os.path.join(CAT_SOUNDS_FOLDER, "*.wav"))
    if not cat_files:
        return
    cat_file = random.choice(cat_files)
    data, sr = sf.read(cat_file, dtype="float32")
    play_audio(data, sr)

def speak(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_monolingual_v1"}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("TTS failed:", r.text)
        return
    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    # Play TTS first
    play_audio(data, sr)
    # Then random cat sound
    play_cat_sound()

# ---------------------------- MAIN ----------------------------
print("\nVoice agent ready! Speak into your mic.")
print("Press Enter to start recording a message, Ctrl+C to exit.\n")

try:
    while True:
        input("Press Enter to record...")
        audio_np = record_audio(RECORD_SECONDS, DEFAULT_SR)
        # STT
        wav_file = "temp.wav"
        sf.write(wav_file, audio_np, DEFAULT_SR)
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": API_KEY}
        files = {"file": ("temp.wav", open(wav_file, "rb"), "audio/wav")}
        data = {"model_id": "scribe_v2"}
        r = requests.post(url, headers=headers, files=files, data=data)
        if r.status_code != 200:
            print("STT failed:", r.text)
            continue
        user_text = r.json().get("text", "")
        if not user_text:
            print("No speech detected.")
            continue
        print(f"\nYOU: {user_text}")
        # Agent reply
        url_agent = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation"
        payload_agent = {
            "simulation_specification": {
                "simulated_user_config": {"first_message": user_text, "language": "en"},
                "agent_config": {"persona": "Toxic cat AI"}
            },
            "new_turns_limit": 1
        }
        r_agent = requests.post(url_agent, headers=headers, json=payload_agent)
        if r_agent.status_code != 200:
            print("Agent failed:", r_agent.text)
            continue
        turns = r_agent.json().get("simulated_conversation", [])
        reply_text = ""
        for turn in turns:
            if turn.get("role") == "agent":
                reply_text = turn.get("message", "").replace("[sarcastic]", "").strip()
        print(f"CAT AI: {reply_text}\n")
        speak(reply_text)

except KeyboardInterrupt:
    print("\nExiting. Bye!")
