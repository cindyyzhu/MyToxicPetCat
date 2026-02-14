import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import resampy
from elevenlabs import ElevenLabs

# ----------------------------
# Load ElevenLabs API key
# ----------------------------
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("Please set the ELEVENLABS_API_KEY environment variable!")

eleven = ElevenLabs(api_key=api_key)
voice_name = "Bella"  # change as desired

# ----------------------------
# Audio recording configuration
# ----------------------------
record_seconds = 4
target_sample_rate = 16000  # for ElevenLabs

# List devices
print("Available audio devices:")
print(sd.query_devices())

# Use default input device
input_device = sd.default.device[0]  # default input device
device_info = sd.query_devices(input_device)
mic_sample_rate = int(device_info['default_samplerate'])
print(f"Using input device: {device_info['name']} (default rate: {mic_sample_rate} Hz)")

# ----------------------------
# Record audio using supported sample rate
# ----------------------------
print("Speak now...")
audio_np = sd.rec(int(record_seconds * mic_sample_rate),
                  samplerate=mic_sample_rate,
                  channels=1,
                  dtype='float32')
sd.wait()
audio_np = audio_np.flatten()

# ----------------------------
# Resample to 16 kHz if needed
# ----------------------------
if mic_sample_rate != target_sample_rate:
    audio_resampled = resampy.resample(audio_np, mic_sample_rate, target_sample_rate)
else:
    audio_resampled = audio_np

# Save recorded audio
wav_file = "usb_mic_record.wav"
sf.write(wav_file, audio_resampled, target_sample_rate)
print(f"Audio recorded and saved as {wav_file}")

# ----------------------------
# Generate speech via ElevenLabs
# ----------------------------
text_to_speak = "Hello! This is your USB microphone speaking."
audio_bytes = eleven.text_to_speech(
    text=text_to_speak,
    voice=voice_name,
    model="eleven_monolingual_v1"
)

output_file = "output.wav"
with open(output_file, "wb") as f:
    f.write(audio_bytes)
print(f"Speech generated! Saved as {output_file}")

# ----------------------------
# Playback generated speech
# ----------------------------
data, sr = sf.read(output_file, dtype='float32')
sd.play(data, sr)
sd.wait()
print("Playback finished!")
