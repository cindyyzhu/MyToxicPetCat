import os
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()
client = ElevenLabs()

# ---------- record ----------

print("Speak now...")
audio_data = sd.rec(int(4 * 16000), samplerate=16000, channels=1)
sd.wait()
sf.write("input.wav", audio_data, 16000)

# ---------- speech to text ----------

r = sr.Recognizer()
with sr.AudioFile("input.wav") as source:
audio = r.record(source)

try:
    text = r.recognize_google(audio)
    print("You said:", text)
except:
    text = "Hello"
    print("Could not understand audio")

# ---------- simple agent reply ----------

reply = f"You said {text}. I am your Raspberry Pi voice agent."

# ---------- elevenlabs TTS ----------

audio_stream = client.text_to_speech.convert(
voice_id="Rachel",
model_id="eleven_multilingual_v2",
text=reply
)

with open("reply.mp3", "wb") as f:
for chunk in audio_stream:
f.write(chunk)

# ---------- play ----------

os.system("ffplay -autoexit -loglevel quiet reply.mp3")
