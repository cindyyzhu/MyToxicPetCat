# ============================ IMPORTS ============================
import os
import time
import glob
import random
import threading
import requests
import numpy as np
import sounddevice as sd
import soundfile as sf
from io import BytesIO
import RPi.GPIO as GPIO

# ============================ CONFIG =============================
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise ValueError("Set ELEVENLABS_API_KEY environment variable!")

AGENT_ID = "agent_1601khf3r1jfff2saez29f6frfny"
VOICE_ID = "XdflFrQO8wbGpWMNZHFr"

RECORD_SECONDS = 5
CAT_SOUNDS_BASE = "cat_sounds"

EMOTIONS = {
    "purr": {"folder": "purr", "motor": "gentle"},
    "meow": {"folder": "meow", "motor": "alert"},
    "hiss": {"folder": "hiss", "motor": "angry"}
}

# ====================== AUDIO DEVICE SETUP =======================
sd.default.device = None
DEFAULT_SR = int(sd.query_devices(kind="output")["default_samplerate"])

# ====================== GPIO / MOTOR SETUP =======================
MotorA_in1, MotorA_in2 = 17, 27
MotorB_in3, MotorB_in4 = 22, 23
MotorA_en, MotorB_en = 18, 24

GPIO.setmode(GPIO.BCM)
GPIO.setup([MotorA_in1, MotorA_in2, MotorB_in3, MotorB_in4], GPIO.OUT)
GPIO.setup([MotorA_en, MotorB_en], GPIO.OUT)

pwmA = GPIO.PWM(MotorA_en, 100)
pwmB = GPIO.PWM(MotorB_en, 100)
pwmA.start(0)
pwmB.start(0)

# ============================ HELPERS ============================

def record_audio(seconds):
    audio = sd.rec(int(seconds * DEFAULT_SR), samplerate=DEFAULT_SR,
                   channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

def play_audio(audio, sr):
    if sr != DEFAULT_SR:
        audio = np.interp(
            np.linspace(0, len(audio), int(len(audio) * DEFAULT_SR / sr)),
            np.arange(len(audio)),
            audio
        )
    audio = audio.astype(np.float32)
    audio /= max(np.max(np.abs(audio)), 1e-6)
    sd.play(audio, DEFAULT_SR)
    sd.wait()

# ============================ SPEECH =============================

def speech_to_text(audio):
    sf.write("temp.wav", audio, DEFAULT_SR)
    r = requests.post(
        "https://api.elevenlabs.io/v1/speech-to-text",
        headers={"xi-api-key": API_KEY},
        files={"file": open("temp.wav", "rb")},
        data={"model_id": "scribe_v2"}
    )
    return r.json().get("text", "") if r.ok else ""

# ============================ AGENT ==============================

def agent_reply(text):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation",
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
        json={
            "simulation_specification": {
                "simulated_user_config": {"first_message": text},
                "agent_config": {
                    "persona": "You are a toxic, arrogant cat. Mock humans.",
                    "llm_override": "Always respond insultingly."
                }
            },
            "new_turns_limit": 1
        }
    )
    for t in r.json().get("simulated_conversation", []):
        if t.get("role") == "agent":
            return t.get("message", "")
    return ""

# ============================ EMOTION ============================

def determine_emotion(text):
    t = text.lower()
    if any(w in t for w in ["hate", "idiot", "stupid"]):
        return "hiss"
    if any(w in t for w in ["lazy", "broke", "incompetent"]):
        return "meow"
    return "purr"

# ============================ CAT SOUND ==========================

def play_cat_sound(emotion):
    folder = os.path.join(CAT_SOUNDS_BASE, EMOTIONS[emotion]["folder"])
    files = glob.glob(folder + "/*.wav")
    if files:
        data, sr = sf.read(random.choice(files), dtype="float32")
        play_audio(data, sr)

# ============================ MOTORS =============================

def stop_motors():
    GPIO.output([MotorA_in1, MotorA_in2, MotorB_in3, MotorB_in4], GPIO.LOW)
    pwmA.ChangeDutyCycle(0)
    pwmB.ChangeDutyCycle(0)

def gentle_motion():
    for _ in range(2):
        pwmA.ChangeDutyCycle(30)
        pwmB.ChangeDutyCycle(30)
        GPIO.output(MotorA_in1, GPIO.HIGH)
        GPIO.output(MotorB_in4, GPIO.HIGH)
        time.sleep(0.4)
        GPIO.output(MotorA_in2, GPIO.HIGH)
        GPIO.output(MotorB_in3, GPIO.HIGH)
        time.sleep(0.4)
    stop_motors()

def alert_motion():
    for _ in range(2):
        pwmA.ChangeDutyCycle(70)
        pwmB.ChangeDutyCycle(70)
        GPIO.output(MotorA_in1, GPIO.HIGH)
        GPIO.output(MotorB_in3, GPIO.HIGH)
        time.sleep(0.2)
        stop_motors()
        time.sleep(0.1)

def angry_motion():
    for _ in range(3):
        pwmA.ChangeDutyCycle(100)
        pwmB.ChangeDutyCycle(100)
        GPIO.output(MotorA_in1, GPIO.HIGH)
        GPIO.output(MotorB_in4, GPIO.HIGH)
        time.sleep(0.15)
        stop_motors()

def perform_motion(emotion):
    {"purr": gentle_motion,
     "meow": alert_motion,
     "hiss": angry_motion}[emotion]()

# ============================ SPEAK ==============================

def speak(text):
    emotion = determine_emotion(text)
    play_cat_sound(emotion)

    threading.Thread(
        target=perform_motion, args=(emotion,), daemon=True
    ).start()

    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/wav"
        },
        json={"text": text, "model_id": "eleven_monolingual_v1"}
    )

    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    play_audio(data, sr)

# ============================ MAIN ===============================

print("\n🐱 Cat AI Ready. Press Enter to talk.\n")

try:
    while True:
        input("Press Enter to speak...")
        audio = record_audio(RECORD_SECONDS)
        user_text = speech_to_text(audio)
        if not user_text:
            continue
        print("YOU:", user_text)

        reply = agent_reply(user_text)
        print("CAT:", reply)
        speak(reply)

except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    stop_motors()
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()
