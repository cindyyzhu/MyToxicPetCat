import os
import sounddevice as sd
import numpy as np
from elevenlabs import set_api_key, generate, play
import keyboard  # to detect keypress

# Load your API key from environment variable
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("Please set the ELEVENLABS_API_KEY environment variable!")

set_api_key(api_key)

samplerate = 16000  # Hz
channels = 1

print("Speak now... Press any key to stop recording.")

# Preallocate a buffer for max 60 seconds (adjust if you want)
max_duration = 60
audio_data = np.zeros((max_duration * samplerate, channels), dtype=np.float32)

# Start recording in the background
recording = sd.InputStream(samplerate=samplerate, channels=channels)
recording.start()

frame_index = 0
try:
    while True:
        # read in chunks of 1024 frames
        frames, _ = recording.read(1024)
        end_index = frame_index + frames.shape[0]
        if end_index > audio_data.shape[0]:
            # stop if buffer full
            print("Maximum recording duration reached.")
            break
        audio_data[frame_index:end_index] = frames
        frame_index = end_index

        if keyboard.is_pressed():
            print("Key pressed, stopping recording...")
            break
finally:
    recording.stop()
    recording.close()

# Trim unused buffer
audio_data = audio_data[:frame_index]

# Convert to 16-bit PCM (required by most TTS APIs)
audio_int16 = np.int16(audio_data * 32767)

# Generate and play response
voice_name = "alloy"  # or choose another voice from ElevenLabs
text_to_speak = "Hello! This is your voice agent speaking back."

audio = generate(text=text_to_speak, voice=voice_name, model="eleven_multilingual_v1")
play(audio)

print("Done!")
