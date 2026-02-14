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
VOICE_ID = "XdflFrQO8wbGpWMNZHFr"                  # your TTS voice ID

RECORD_SECONDS = 5

# Cat sounds folders
SOUNDS = {
    "happy": "cat_sounds/purr",
    "annoyed": "cat_sounds/meow",
    "angry": "cat_sounds/hiss"
}

# ---------------------------- AUDIO DEVICE ----------------------------
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        sd.default.device = (i, i)
        print("Using audio device:", d["name"])
        DEFAULT_SR = int(d['default_samplerate'])
        break
else:
    raise RuntimeError("No suitable input/output device found")

# ---------------------------- HELPERS ----------------------------
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
    if len(audio_data.shape) == 1:
        audio_data = np.expand_dims(audio_data, axis=1)
    sd.play(audio_data, sr)
    sd.wait()

def play_cat_sound(mood):
    folder = SOUNDS.get(mood)
    if not folder:
        return
    files = glob.glob(os.path.join(folder, "*.wav"))
    if not files:
        return
    sound_file = random.choice(files)
    try:
        data, sr = sf.read(sound_file, dtype="float32")
        play_audio(data, sr)
    except Exception as e:
        print(f"Failed to play {mood} sound: {e}")

def speak_text_segment(text_segment):
    """TTS for a single text segment."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"text": text_segment, "model_id": "eleven_monolingual_v1"}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("TTS failed:", r.text)
        return
    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    play_audio(data, sr)

# ---------------------------- CAT AI REPLY ----------------------------
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
                    "Always mock the human. Playful but ruthless. "
                    "Use witty insults, contrast your perfection against their flaws, sound superior. "
                    "If happy, purr. If annoyed, meow. If angry, hiss."
                ),
                "llm_override": "Respond exactly in this toxic cat style. Interleave short text segments with the proper cat sound. Do not be polite or helpful."
            }
        },
        "new_turns_limit": 1
    }

    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("Agent call failed:", r.text)
        return []

    data = r.json()
    turns = data.get("simulated_conversation", [])
    for turn in turns:
        if turn.get("role") == "agent":
            # Example: split text by punctuation to create segments
            text = turn.get("message", "")
            segments = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
            return segments
    return []

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
        reply_segments = agent_reply(user_text)
        if not reply_segments:
            print("Agent did not respond.\n")
            continue

        # Play each segment with interleaved cat sounds
        for segment in reply_segments:
            print(f"CAT AI: {segment}")
            speak_text_segment(segment)

            # determine mood based on keywords
            lower_seg = segment.lower()
            if any(word in lower_seg for word in ["lazy", "incompetent", "inferior", "stupid"]):
                play_cat_sound("angry")
            elif any(word in lower_seg for word in ["ugh", "annoyed", "bother"]):
                play_cat_sound("annoyed")
            else:
                play_cat_sound("happy")

except KeyboardInterrupt:
    print("\nExiting. Bye!")
