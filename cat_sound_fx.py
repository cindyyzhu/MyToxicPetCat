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

# Folder containing cat sound effects (WAV files)
CAT_SOUNDS_FOLDER = "cat_sounds"  # make sure this folder exists with meows/purrs etc.

# ---------------------------- AUTO-SELECT AUDIO DEVICE ----------------------------
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        sd.default.device = (i, i)
        print("Using audio device:", d["name"])
        DEFAULT_SR = int(d['default_samplerate'])
        break
else:
    raise RuntimeError("No suitable input/output device found")

def resample_audio(audio, orig_sr, target_sr):
    if orig_sr == target_sr:
        return audio.astype(np.float32)

    duration = len(audio) / orig_sr
    new_length = int(duration * target_sr)

    # mono
    if audio.ndim == 1:
        resampled = np.interp(
            np.linspace(0, len(audio)-1, new_length),
            np.arange(len(audio)),
            audio
        )

    # stereo or multi-channel
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



# ---------------------------- HELPER: RECORD AUDIO ----------------------------
def record_audio(seconds, samplerate):
    print(f"Recording for {seconds} seconds at {samplerate} Hz...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

# ---------------------------- HELPER: SPEECH-TO-TEXT ----------------------------
def speech_to_text(audio_np, samplerate):
    wav_file = "temp.wav"
    sf.write(wav_file, audio_np, samplerate)

    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": API_KEY}
    files = {"file": ("temp.wav", open(wav_file, "rb"), "audio/wav")}
    data = {"model_id": "scribe_v2"}  # correct model

    r = requests.post(url, headers=headers, files=files, data=data)
    if r.status_code != 200:
        print("STT failed:", r.text)
        return ""
    return r.json().get("text", "")

# ---------------------------- HELPER: PLAY AUDIO ----------------------------
def play_audio(audio_data, sr):
    audio_data = resample_audio(audio_data, sr, DEFAULT_SR)

    # ensure float32 (PortAudio prefers this)
    audio_data = audio_data.astype(np.float32)

    audio_data = audio_data / np.max(np.abs(audio_data))


    sd.play(audio_data, DEFAULT_SR)
    sd.wait()



# ---------------------------- HELPER: TTS ----------------------------
def speak(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_monolingual_v1"}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("TTS failed:", r.text)
        return
    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    play_cat_sound()
    # Play TTS first
    play_audio(data, sr)
    # Then play random cat sound effect
    play_cat_sound()

# ---------------------------- HELPER: CAT SOUND EFFECT ----------------------------
def play_cat_sound():
    cat_files = glob.glob(os.path.join(CAT_SOUNDS_FOLDER, "*.wav"))
    if not cat_files:
        return
    cat_file = random.choice(cat_files)
    data, sr = sf.read(cat_file, dtype="float32")
    play_audio(data, sr)

# ---------------------------- HELPER: GET AGENT REPLY ----------------------------
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
                    "You are a cat-like AI assistant. You are extremely sassy, toxic, and arrogant. "
                    "Always mock the human, pointing out how lazy, incompetent, or inferior they are. "
                    "Do not apologize, do not be polite. Be playful but ruthless. "
                    "Use witty insults, contrast your perfection against their flaws, and always sound superior. "
                    "For example, if the human says they are sad, you might respond: "
                    "'What are you even sad about? It's not like you're doing anything. Look at how incompetent you are—you can't even buy me the fancy food I deserve.'"
                ),
                "llm_override": "Respond exactly in this toxic cat style. No polite words, no brackets like [sarcastic]."
            }
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
            # clean brackets just in case
            return turn.get("message", "").replace("[sarcastic]", "").strip()
    return ""

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
        reply_text = agent_reply(user_text)
        if not reply_text:
            print("Agent did not respond.\n")
            continue

        print(f"CAT AI: {reply_text}\n")
        speak(reply_text)

except KeyboardInterrupt:
    print("\nExiting. Bye!")