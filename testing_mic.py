import sounddevice as sd
import numpy as np
import wavio

# Parameters
duration = 5  # seconds
fs = 44100    # sampling rate

print("Recording...")
audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()  # Wait until recording is finished
print("Recording done!")

# Save to a WAV file (optional)
wavio.write("output.wav", audio, fs, sampwidth=2)

# Play back the recorded audio
print("Playing back...")
sd.play(audio, fs)
sd.wait()
print("Playback finished!")
