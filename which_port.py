import sounddevice as sd

record_seconds = 3

# Pick your USB Audio Device (input & output)
usb_device_index = 2  # replace with your actual USB device index

# Query device info
device_info = sd.query_devices(usb_device_index)
sample_rate = int(device_info['default_samplerate'])
print(f"Using device: {device_info['name']} at {sample_rate} Hz")

# Record audio
print("Speak now...")
audio = sd.rec(int(record_seconds * sample_rate),
               samplerate=sample_rate,
               channels=1,
               dtype='float32',
               device=usb_device_index)
sd.wait()
print("Recording finished!")

# Playback using the same USB device
print("Playing back...")
sd.play(audio, samplerate=sample_rate, device=usb_device_index)
sd.wait()
print("Playback finished!")
