import sounddevice as sd
import numpy as np

# ----------------------------
# Configuration
# ----------------------------
record_seconds = 3  # seconds to record

# List all audio devices
print("Available audio devices:")
print(sd.query_devices())

# Use default input/output devices (or pick a device index from the list)
input_device = sd.default.device[0]   # 0=input
output_device = sd.default.device[1]  # 1=output

device_info = sd.query_devices(input_device)
sample_rate = int(device_info['default_samplerate'])

print(f"Recording from: {device_info['name']} at {sample_rate} Hz")
print("Speak now...")

# ----------------------------
# Record audio
# ----------------------------
audio = sd.rec(int(record_seconds * sample_rate),
               samplerate=sample_rate,
               channels=1,
               dtype='float32')
sd.wait()
audio = audio.flatten()
print("Recording finished!")

# ----------------------------
# Playback audio
# ----------------------------
print("Playing back...")
sd.play(audio, sample_rate)
sd.wait()
print("Playback finished!")
