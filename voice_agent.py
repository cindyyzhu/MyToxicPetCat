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

# ----------------------------
# Auto-detect device with both input & output
# ----------------------------
devices = sd.query_devices()
selected_device = None
for idx, dev in enumerate(devices):
    if dev['max_input_channels'] > 0 and dev['max_output_channels'] > 0:
        selected_device = idx
        break

if selected_device is None:
    raise RuntimeError("No audio device found with both input and output channels!")

device_info = devices[selected_device]
mic_sample_rate = int(device_info['default_samplerate'])
out_channels = min(2, device_info['max_output_channels'])  # playback in stereo if possible

print(f"Using device: {device_info['name']} (index {selected_device})")
print(f"Mic sample rate: {mic_sample_rate} Hz, Playback channels: {out_channels}")

# ----------------------------
# Record audio
# ----------------------------
print("Speak now...")
audio_np = sd.rec(int(record_seconds * mic_sample_rate),
                  samplerate=mic_sample_rate,
                  channels=1,
                  dtype='float32',
                  device=selected_device)
sd.wait()
audio_np = audio_np.flatten()
print("Recording finished!")

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

# ----------------------------
# Generate speech via ElevenLabs
# ----------------------------
# Use the text_to_speech.convert method
audio_bytes = eleven.text_to_speech.convert(
    text=text_to_speak,
    voice_id=voice_name,
    model_id="eleven_monolingual_v1",
    output_format="wav_16000"  # request raw WAV at 16 kHz
)

output_file = "output.wav"
with open(output_file, "wb") as f:
    f.write(audio_bytes)
print(f"Speech generated! Saved as {output_file}")

# ----------------------------
# Playback generated speech
# ----------------------------
data, sr = sf.read(output_file, dtype='float32')

# Convert mono to stereo if needed
if out_channels == 2 and data.ndim == 1:
    data = np.stack([data, data], axis=-1)

print("Playing back generated speech...")
sd.play(data, sr, device=selected_device, blocking=True)
print("Playback finished!")
