import os
import numpy as np
import sounddevice as sd
import soundfile as sf
from elevenlabs import ElevenLabs

# ----------------------------
# Load API key from environment
# ----------------------------
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("Please set the ELEVENLABS_API_KEY environment variable!")

eleven = ElevenLabs(api_key=api_key)
voice_name = "Bella"  # change as desired

# ----------------------------
# Recording configuration
# ----------------------------
sample_rate = 16000      # target sample rate for ElevenLabs
record_seconds = 4       # seconds to record

print("Speak now...")

# Record audio from default USB microphone
audio_np = sd.rec(int(record_seconds * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
sd.wait()  # wait until recording is finished

# Flatten in case audio is 2D
audio_np = audio_np.flatten()

# Save to temporary WAV
wav_file = "usb_mic_record.wav"
sf.write(wav_file, audio_np, sample_rate)

print("Audio captured! Sending to ElevenLabs...")

# ----------------------------
# Generate speech via ElevenLabs
# ----------------------------
text_to_speak = "Hello! This is your USB microphone speaking."

audio_bytes = eleven.text_to_speech(
    text=text_to_speak,
    voice=voice_name,
    model="eleven_monolingual_v1"
)

# Save audio output
output_file = "output.wav"
with open(output_file, "wb") as f:
    f.write(audio_bytes)

print(f"Speech generated! Saved as {output_file}")

# ----------------------------
# Play back audio
# ----------------------------
data, sr = sf.read(output_file, dtype='float32')
sd.play(data, sr)
sd.wait()
print("Playback finished!")
