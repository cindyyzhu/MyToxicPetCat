import sounddevice as sd
import numpy as np

record_seconds = 3

# Auto-detect device with both input & output
devices = sd.query_devices()
selected_device = None

for idx, dev in enumerate(devices):
    if dev['max_input_channels'] > 0 and dev['max_output_channels'] > 0:
        selected_device = idx
        break

if selected_device is None:
    raise RuntimeError("No device with both input and output channels found!")

device_info = devices[selected_device]
sample_rate = int(device_info['default_samplerate'])
out_channels = min(2, device_info['max_output_channels'])  # play stereo if available

print(f"Using device: {device_info['name']} (index {selected_device}) at {sample_rate} Hz")
print(f"Playback channels: {out_channels}")

# Record audio (mono)
print("Speak now...")
audio = sd.rec(int(record_seconds * sample_rate),
               samplerate=sample_rate,
               channels=1,
               dtype='float32',
               device=selected_device)
sd.wait()
audio = audio.flatten()
print("Recording finished!")

# Convert mono to stereo if device expects 2 channels
if out_channels == 2:
    audio = np.stack([audio, audio], axis=-1)

# Playback
print("Playing back...")
sd.play(audio, samplerate=sample_rate, device=selected_device, blocking=True)
print("Playback finished!")
