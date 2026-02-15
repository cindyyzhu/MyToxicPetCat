import asyncio
import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
import sounddevice as sd
import numpy as np

# -----------------------------
# Configuration
# -----------------------------
HTTP_PORT = 8000
WS_PORT = 8765
DEFAULT_SR = 44100

# -----------------------------
# Frontend HTML
# -----------------------------
FRONTEND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My Toxic Pet Cat</title>
<!-- Include your full HTML here -->
</head>
<body>
<h1>My Toxic Pet Cat</h1>
<div id="speechText"></div>
<script>
const ws = new WebSocket('ws://localhost:8765');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const textEl = document.getElementById('speechText');
    if(data.response) textEl.textContent = data.response;
};
ws.onopen = () => console.log("Connected to backend");
</script>
</body>
</html>
"""

# -----------------------------
# HTTP Server
# -----------------------------
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(FRONTEND_HTML.encode("utf-8"))

def start_http_server():
    server = HTTPServer(("0.0.0.0", HTTP_PORT), MyHandler)
    print(f"🌐 UI → http://localhost:{HTTP_PORT}")
    server.serve_forever()

# -----------------------------
# STT / TTS Placeholders
# -----------------------------
def record_audio(duration=5):
    print(f"Recording for {duration}s...")
    audio = sd.rec(int(duration * DEFAULT_SR), samplerate=DEFAULT_SR, channels=1)
    sd.wait()
    return audio.flatten()

def mock_speech_to_text(audio):
    # Replace with real STT call
    return "Hello from your toxic cat!"

def mock_text_to_speech(text):
    # Replace with real TTS call
    print("TTS:", text)
    return np.zeros(44100)  # dummy audio

async def ws_handler(websocket):
    while True:
        # Wait for a message from frontend if needed
        try:
            msg = await websocket.recv()  # not used here, just a placeholder
        except websockets.ConnectionClosed:
            print("Client disconnected")
            break

        # Record audio and convert to text
        audio = record_audio(3)
        user_text = mock_speech_to_text(audio)

        # Generate a reply
        reply_text = f"Cat says: {user_text}"

        # Send to frontend
        await websocket.send(json.dumps({"response": reply_text, "mood": "responding"}))

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    # Start HTTP server in separate thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    # Start WebSocket server
    asyncio.run(websockets.serve(ws_handler, "0.0.0.0", WS_PORT))
    print(f"WebSocket server running on ws://localhost:{WS_PORT}")

    # Keep main thread alive
    asyncio.get_event_loop().run_forever()
