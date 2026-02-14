import sounddevice as sd

record_seconds = 3

# Pick your USB mic and speakers
input_device_index = 2   # USB Audio Device input
output_device_index = 0  # BCM2835 Headphones output

device_info = sd.query_devices(input_device_index)
sample_rate = int(device_info['default_samplerate'])

print(f"Recording from: {device_info['name']} at {sample_rate} Hz")
audio = sd.rec(int(record_seconds * sample_rate), samplerate=sample_rate,
               channels=1, dtype='float32', device=input_device_index)
sd.wait()
print("Recording finished!")

print("Playing back...")
sd.play(audio, sample_rate, device=output_device_index)
sd.wait()
print("Playback finished!")
