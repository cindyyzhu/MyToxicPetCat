import os
import sounddevice as sd
import numpy as np
from elevenlabs import ElevenLabs, Voice
import keyboard  # to detect keypress

# Make sure the API key is set in your environment
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("Please set the ELEVENLABS_API_KEY environment variable!")

# Initialize the ElevenLabs client (no arguments)
client = ElevenLabs()

samplerate = 16000  # Hz
channels = 1

print("Speak now... Press any key to stop recording.")

# Preallocate buffer for max 60 seconds
max_duration = 60
audio_data = np.zeros((max_duration * samplerate, channels), dtype=np.float32)

# Start recording
recording = sd.InputStream(samplerate=samplerate, channels=channels)
recording.start()

frame_index = 0
try:
    while True:
        frames, _ = recording.read(1024)
        end_index = frame_index + frames.shape[0]
        if end_index > audio_data.shape[0]:
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

# Convert to 16-bit PCM
audio_int16 = np.int16(audio_data * 32767)

# Generate and play response
voice_name = "alloy"  # or any available voice
text_to_speak = "Hello! This is your voice agent speaking back."

# Get the voice object
voice: Voice = client.get_voices_by_name(voice_name)[0]

# Generate audio from text
audio_bytes = voice.generate(text=text_to_speak)

# Play audio
voice.play(audio_bytes)

print("Done!")
