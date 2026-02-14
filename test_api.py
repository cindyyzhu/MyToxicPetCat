# test_elevenlabs.py
import os
from elevenlabs import ElevenLabs

api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("Set ELEVENLABS_API_KEY environment variable!")

client = ElevenLabs()
print("ElevenLabs client initialized successfully!")
