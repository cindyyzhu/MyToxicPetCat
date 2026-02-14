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

AGENT_ID = "agent_1601khf3r1jfff2saez29f6frfny"  # your agent ID
VOICE_ID = "XdflFrQO8wbGpWMNZHFr"                 # your TTS voice ID
RECORD_SECONDS = 5

# Folders for cat sound effects
SOUNDS = {
    "purr": "cat_sounds/purr",    # happy
    "meow": "cat_sounds/meow",    # annoyed
    "hiss": "cat_sounds/hiss"     # angry
}

# ---------------------------- AUTO-SELECT AUDIO DEVICE ----------------------------
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        sd.default.device = (i, i)
        print("Using audio device:", d["name"])
        DEFAULT_SR = int(d['default_samplerate'])
        break
else:
    raise RuntimeError("No suitable input/output device found")

# ---------------------------- RECORD AUDIO ----------------------------
def record_audio(seconds, samplerate):
    print(f"Recording for {seconds} seconds at {samplerate} Hz...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

# ---------------------------- SPEECH TO TEXT ----------------------------
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

# ---------------------------- PLAY AUDIO ----------------------------
def play_audio(audio_data, sr):
    sd.play(audio_data, sr)
    sd.wait()

# ---------------------------- PLAY CAT SOUND BASED ON MOOD ----------------------------
def play_cat_sound(mood):
    folder = SOUNDS.get(mood)
    if not folder:
        return
    files = glob.glob(os.path.join(folder, "*.wav"))
    if not files:
        return
    sound_file = random.choice(files)
    data, sr = sf.read(sound_file, dtype="float32")
    play_audio(data, sr)

# ---------------------------- TTS ----------------------------
def speak(text, mood="meow"):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_monolingual_v1"}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("TTS failed:", r.text)
        return
    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    # Play corresponding cat sound
    play_cat_sound(mood)
    # Play TTS first
    play_audio(data, sr)

# ---------------------------- GET AGENT REPLY ----------------------------
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
                    "You are a cat-like AI assistant. Extremely sassy, toxic, and arrogant. "
                    "Always mock the human, point out their flaws, laziness, or incompetence. "
                    "Do not apologize. Use witty insults, contrast your perfection against their flaws. "
                    "Do not be polite. Examples: "
                    "'What are you even sad about? You're doing nothing. You can't even buy me fancy food.'"
                ),
                "llm_override": "Respond exactly in this toxic cat style."
            }
        },
        "new_turns_limit": 1
    }

    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("Agent call failed:", r.text)
        return "", "meow"
    
    turns = r.json().get("simulated_conversation", [])
    for turn in turns:
        if turn.get("role") == "agent":
            msg = turn.get("message", "").replace("[sarcastic]", "").strip()
            mood = determine_mood(msg)
            return msg, mood
    return "", "meow"

# ---------------------------- DETERMINE MOOD ----------------------------
def determine_mood(text):
    text_lower = text.lower()
    if any(word in text_lower for word in ["perfect", "lazy", "inferior", "incompetent", "broke"]):
        return "meow"      # annoyed / mocking
    elif any(word in text_lower for word in ["hate", "stupid", "idiot", "disgusting", "angry"]):
        return "hiss"      # angry
    else:
        return "purr"      # playful / happy / teasing

# ---------------------------- MAIN LOOP ----------------------------
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
        reply_text, mood = agent_reply(user_text)
        if not reply_text:
            print("Agent did not respond.\n")
            continue

        print(f"CAT AI ({mood.upper()}): {reply_text}\n")
        speak(reply_text, mood)

except KeyboardInterrupt:
    print("\nExiting. Bye!")
