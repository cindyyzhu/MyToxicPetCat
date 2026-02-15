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

def play_audio_dont_wait(audio_data, sr):
    audio_data = resample_audio(audio_data, sr, DEFAULT_SR)

    # ensure float32 (PortAudio prefers this)
    audio_data = audio_data.astype(np.float32)

    audio_data = audio_data / np.max(np.abs(audio_data))


    sd.play(audio_data, DEFAULT_SR)

# ---------------------------- HELPER: TTS ----------------------------
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

# ---------------------------- HELPER: CALCULATE AMPLITUDE ENVELOPE ----------------------------
def get_amplitude_envelope(data, sr, fps=30):
    """
    Takes raw audio data and returns a list of volume levels synced to a framerate.
    """
    # 1. Calculate how many audio samples fit into one "frame" of movement
    chunk_size = sr // fps
    
    # 2. Ensure data is 1D (Mono). If it's stereo, average the two channels.
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
        
    # 3. Truncate the end of the audio array so it divides perfectly into our chunks
    num_chunks = len(data) // chunk_size
    truncated_data = data[:num_chunks * chunk_size]
    
    # 4. Reshape the flat array into a 2D array of chunks
    chunks = truncated_data.reshape(num_chunks, chunk_size)
    
    # 5. Calculate the RMS (volume) for each chunk
    # Square the data, find the mean of each chunk, then get the square root
    rms_values = np.sqrt(np.mean(chunks**2, axis=1))
    
    # 6. Normalize the values to be between 0.0 and 1.0
    # This makes it infinitely easier to map to motor speeds or PWM duty cycles later
    max_rms = np.max(rms_values)
    if max_rms > 0:
        normalized_rms = rms_values / max_rms
    else:
        normalized_rms = rms_values
        
    return normalized_rms

# ---------------------------- HELPER: PLAY SOUND AND MOVE MOTORS ----------------------------

def play_cat_sound_and_move_motor(data, sr):
    # 1. Play intro sound
    play_cat_sound()
    
    # 2. Get the pre-calculated volume chunks
    fps = 30 # Updates 30 times per second
    amplitudes = get_amplitude_envelope(data, sr, fps=fps)
    delay_between_frames = 1.0 / fps
    
    print("Starting to 'lip sync'")
    
    # 3. START AUDIO ONCE (It plays in the background)
    play_audio_dont_wait(data, sr)
    
    # 4. Loop through the pre-calculated motor speeds
    for amp in amplitudes:
        start_time = time.time()
        
        # 4. Loop through the pre-calculated motor speeds

    if amp > 0.1:
        speed = int(40 + amp * 60)   # 40–100 safe range

        # pick a motion pattern based on frame index
        pattern = i % 6

        # --- PATTERN 0: normal forward ---
        if pattern == 0:
            motorA_forward(speed=speed)
            motorB_forward(speed=speed)

        # --- PATTERN 1: reverse burst ---
        elif pattern == 1:
            motorA_backward(speed=speed)
            motorB_backward(speed=speed)

        # --- PATTERN 2: spin in place ---
        elif pattern == 2:
            motorA_forward(speed=speed)
            motorB_backward(speed=speed)

        # --- PATTERN 3: opposite spin ---
        elif pattern == 3:
            motorA_backward(speed=speed)
            motorB_forward(speed=speed)

        # --- PATTERN 4: curve left ---
        elif pattern == 4:
            motorA_forward(speed=speed)
            motorB_forward(speed=int(speed * 0.4))

        # --- PATTERN 5: curve right ---
        else:
            motorA_forward(speed=int(speed * 0.4))
            motorB_forward(speed=speed)

        # occasional quick flip for extra personality
        if amp > 0.7 and (i % 10 == 0):
            motorA_backward(speed=80)
            motorB_forward(speed=80)
            time.sleep(0.05)

    else:
        stop_motors()

    # 5. Keep the loop synchronized with the audio track
    elapsed = time.time() - start_time
    time.sleep(max(0, delay_between_frames - elapsed))

        
    # 6. Cleanup
    stop_motors() # Ensure mouth is completely stopped at the end of the sentence
    sd.wait()     # Catch-all to make sure the audio track is 100% finished
    
    # 7. Play outro sound
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
        data, sr = get_speech_from_elevenlabs(reply_text)

        if data is not None and sr is not None:
            play_cat_sound_and_move_motor(data, sr)
        else:
            print("No data was returned.")

except KeyboardInterrupt:
    print("\nExiting. Bye!")
    cleanup_motors()