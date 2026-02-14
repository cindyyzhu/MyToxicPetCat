import sounddevice as sd
import numpy as np

duration = 4  # seconds
samplerate = 16000

print("Speak now...")
audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
sd.wait()  # wait until recording is finished
print("Recording finished!")
