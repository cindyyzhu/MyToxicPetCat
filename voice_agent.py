import serial
import time
import numpy as np
import soundfile as sf
from elevenlabs import generate, play, set_api_key

# ----------------------------
# Set up ElevenLabs API
# ----------------------------
set_api_key("YOUR_ELEVENLABS_API_KEY")  # Replace with your ElevenLabs API key

# ----------------------------
# Serial setup for Arduino
# ----------------------------
arduino_port = "/dev/ttyACM0"  # Change if needed
baud_rate = 115200

ser = serial.Serial(arduino_port, baud_rate, timeout=1)
time.sleep(2)  # wait for Arduino to reset

# ----------------------------
# Recording configuration
# ----------------------------
sample_rate = 16000      # target sample rate for ElevenLabs
record_seconds = 4       # how many seconds to record

print("Speak now...")

samples = []

# Read samples from Arduino
start_time = time.time()
while (time.time() - start_time) < record_seconds:
    line = ser.readline().decode("utf-8", errors="ignore").strip()
    if line:
        try:
            mic_val = int(line)
            # Normalize to float32 between -1.0 and 1.0
            mic_float = (mic_val / 1023.0) * 2 - 1
            samples.append(mic_float)
        except ValueError:
            pass  # skip invalid lines

ser.close()

if not samples:
    print("No audio captured!")
    exit()

# Convert to numpy array
audio_np = np.array(samples, dtype=np.float32)

# Save to temporary WAV
wav_file = "arduino_record.wav"
sf.write(wav_file, audio_np, sample_rate)

print("Audio captured! Sending to ElevenLabs...")

# ----------------------------
# Generate speech via ElevenLabs
# ----------------------------
text_to_speak = "Hello! This is your Arduino microphone speaking."

audio = generate(
    text=text_to_speak,
    voice="Bella",  # change voice as desired
    model="eleven_monolingual_v1"
)

# Play the generated speech
play(audio)
