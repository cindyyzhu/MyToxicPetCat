import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
from io import BytesIO
import random
import glob
import time
from motors_just_fcns import motorA_forward, motorB_forward, stop_motors, cleanup_motors

import asyncio
import websockets
import json
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from http.server import BaseHTTPRequestHandler, HTTPServer

FRONTEND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Toxic Pet Cat</title>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #1a0a2e;
            --bg-mid: #2d1b4e;
            --accent-pink: #ff6b9d;
            --accent-cyan: #00d9ff;
            --accent-yellow: #ffd93d;
            --text-light: #f0f0f0;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'VT323', monospace;
            background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-mid) 100%);
            color: var(--text-light);
            overflow: hidden;
            height: 100vh;
            position: relative;
        }

        /* Scanline effect */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 0, 0, 0.15),
                rgba(0, 0, 0, 0.15) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 1000;
            animation: scanline 8s linear infinite;
        }

        @keyframes scanline {
            0% { transform: translateY(0); }
            100% { transform: translateY(100px); }
        }

        /* Floating particles */
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--accent-cyan);
            opacity: 0.3;
            animation: float 15s infinite ease-in-out;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); }
            50% { transform: translateY(-100vh) translateX(50px); }
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 1;
        }

        .header {
            font-family: 'Press Start 2P', monospace;
            font-size: 24px;
            text-align: center;
            margin-bottom: 20px;
            color: var(--accent-pink);
            text-shadow: 
                0 0 10px var(--accent-pink),
                0 0 20px var(--accent-pink),
                0 0 30px var(--accent-cyan);
            animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
            from { text-shadow: 0 0 10px var(--accent-pink), 0 0 20px var(--accent-pink); }
            to { text-shadow: 0 0 20px var(--accent-pink), 0 0 30px var(--accent-pink), 0 0 40px var(--accent-cyan); }
        }

        .main-content {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 30px;
            align-items: center;
        }

        .cat-display {
            background: rgba(0, 0, 0, 0.4);
            border: 4px solid var(--accent-cyan);
            box-shadow: 
                0 0 20px rgba(0, 217, 255, 0.3),
                inset 0 0 20px rgba(0, 0, 0, 0.5);
            padding: 40px;
            border-radius: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            overflow: hidden;
            min-height: 400px;
        }

        .cat-display::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(135deg, var(--accent-pink), var(--accent-cyan));
            border-radius: 20px;
            z-index: -1;
        }

        .cat-image-container {
            position: relative;
            width: 100%;
            height: 400px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .cat-image {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            animation: catBounce 3s ease-in-out infinite;
            transition: opacity 0.3s ease;
        }

        .cat-video {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            animation: catBounce 3s ease-in-out infinite;
            transition: opacity 0.3s ease;
        }

        .cat-image.hidden,
        .cat-video.hidden {
            opacity: 0;
            position: absolute;
        }

        @keyframes catBounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        .info-panel {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .speech-box {
            background: rgba(0, 0, 0, 0.6);
            border: 3px solid var(--accent-yellow);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 0 15px rgba(255, 217, 61, 0.3);
        }

        .speech-box h2 {
            font-family: 'Press Start 2P', monospace;
            font-size: 14px;
            color: var(--accent-yellow);
            margin-bottom: 15px;
            text-transform: uppercase;
        }

        .speech-text {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            min-height: 150px;
            font-size: 22px;
            line-height: 1.5;
            border-left: 4px solid var(--accent-pink);
            animation: fadeIn 0.5s ease-in;
            font-family: 'Courier New', monospace;
        }

        /* Terminal cursor */
        .speech-text::after {
            content: '█';
            color: var(--accent-cyan);
            animation: blink 1s step-end infinite;
            margin-left: 2px;
        }

        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .mood-indicator {
            margin-top: 15px;
            font-family: 'Press Start 2P', monospace;
            font-size: 12px;
            text-align: center;
            color: var(--accent-cyan);
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .version-info {
            position: absolute;
            bottom: 10px;
            right: 10px;
            font-family: 'Press Start 2P', monospace;
            font-size: 8px;
            color: rgba(255, 255, 255, 0.3);
        }

        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            .header {
                font-size: 18px;
            }
        }
    </style>
</head>
<body>
    <!-- Floating particles -->
    <div class="particle" style="left: 10%; animation-delay: 0s;"></div>
    <div class="particle" style="left: 30%; animation-delay: 2s;"></div>
    <div class="particle" style="left: 50%; animation-delay: 4s;"></div>
    <div class="particle" style="left: 70%; animation-delay: 6s;"></div>
    <div class="particle" style="left: 90%; animation-delay: 8s;"></div>

    <div class="container">
        <div class="header">
            ⟨⟨ MY TOXIC PET CAT ⟩⟩
        </div>

        <div class="main-content">
            <div class="cat-display">
                <div class="cat-image-container" id="catImageContainer">
                    <!-- Cat images/videos will be dynamically loaded here -->
                    <!-- Supports: PNG, JPG, GIF, MP4, WEBM -->
                </div>
            </div>

            <div class="info-panel">
                <div class="speech-box">
                    <h2>💬 Response</h2>
                    <div class="speech-text" id="speechText">
                        
                    </div>
                    <div class="mood-indicator" id="moodIndicator">
                        Current Mood: IDLE
                    </div>
                </div>
            </div>
        </div>

        <div class="version-info">v2.0.0 | Pi-CatBot Custom</div>
    </div>

    <script>
        let currentMood = 'idle';
        
        // Asset paths - using single GIF for responding state
        const assetPaths = {
            idle: 'assets/cat-idle.gif',              // Still image when idle
            responding: 'assets/cat-responding.gif',   // GIF when responding/active
        };

        // Detect file type based on extension
        function getFileType(path) {
            const ext = path.split('.').pop().toLowerCase();
            if (ext === 'mp4' || ext === 'webm' || ext === 'mov') {
                return 'video';
            }
            return 'image'; // png, jpg, gif, webp, svg
        }

        // Create and load assets dynamically
        function createAssetElement(mood, path) {
            const container = document.getElementById('catImageContainer');
            const fileType = getFileType(path);
            let element;

            if (fileType === 'video') {
                element = document.createElement('video');
                element.className = 'cat-video hidden';
                element.loop = true;
                element.muted = true;
                element.playsInline = true;
                element.autoplay = false;
                element.src = path;
            } else {
                element = document.createElement('img');
                element.className = 'cat-image hidden';
                element.src = path;
                element.alt = `${mood} Cat`;
            }

            element.id = `catAsset-${mood}`;
            element.dataset.mood = mood;
            element.dataset.type = fileType;

            // Error handling
            element.onerror = function() {
                console.error(`Failed to load asset for ${mood}: ${path}`);
                this.style.display = 'none';
            };

            // Success handling
            if (fileType === 'image') {
                element.onload = function() {
                    console.log(`✅ Loaded ${mood} image: ${path}`);
                };
            } else {
                element.onloadeddata = function() {
                    console.log(`✅ Loaded ${mood} video: ${path}`);
                };
            }

            container.appendChild(element);
            return element;
        }

        // Load all assets on page load
        window.addEventListener('DOMContentLoaded', () => {
            const container = document.getElementById('catImageContainer');
            container.innerHTML = ''; // Clear container

            console.log('🎬 Loading assets...');

            // Create elements for all moods
            for (const [mood, path] of Object.entries(assetPaths)) {
                createAssetElement(mood, path);
            }

            // Clear speech box initially
            document.getElementById('speechText').textContent = '';
            console.log('🧹 Cleared speech box on load');

            // Show idle by default
            setTimeout(() => {
                const idleElement = document.getElementById('catAsset-idle');
                if (idleElement) {
                    idleElement.classList.remove('hidden');
                    console.log('🐱 Starting in IDLE state');
                    if (idleElement.tagName === 'VIDEO') {
                        idleElement.play().catch(e => console.log('Video autoplay prevented'));
                    }
                } else {
                    console.error('❌ Could not find idle asset!');
                }

                // Start test mode after a brief delay
                setTimeout(() => {
                    console.log('🚀 Test mode starting - will switch to RESPONDING in 1 second...');
                    toggleResponse(); // Trigger first switch to responding
                }, 1000);
            }, 100);
        });

        // Change mood and switch displayed image/video
        function changeMood(mood) {
            console.log(`🔄 Changing mood to: ${mood}`);
            currentMood = mood;
            
            // Get all cat assets (images and videos)
            const allAssets = document.querySelectorAll('.cat-image, .cat-video');
            console.log(`   Found ${allAssets.length} total assets`);
            
            // Hide all and pause videos
            allAssets.forEach(asset => {
                asset.classList.add('hidden');
                if (asset.tagName === 'VIDEO') {
                    asset.pause();
                    asset.currentTime = 0; // Reset video to start
                }
            });
            
            // Show and play the selected mood
            const targetAsset = document.getElementById(`catAsset-${mood}`);
            if (targetAsset) {
                console.log(`   ✅ Found asset for ${mood}, type: ${targetAsset.tagName}`);
                targetAsset.classList.remove('hidden');
                
                // If it's a video, play it
                if (targetAsset.tagName === 'VIDEO') {
                    targetAsset.play().catch(e => {
                        console.error('   ❌ Video play failed:', e);
                    });
                }
            } else {
                console.error(`   ❌ No asset found for mood: ${mood}`);
                console.log(`   Available assets:`, Array.from(allAssets).map(a => a.id));
            }
            
            const moodText = {
                responding: 'RESPONDING',
                idle: 'IDLE'
            };
            
            document.getElementById('moodIndicator').textContent = `Current Mood: ${moodText[mood] || 'UNKNOWN'}`;
            
            // Handle speech box based on mood
            if (mood === 'responding') {
                // Start typing animation
                typeText('AHAHAHA', 150); // 150ms per character
            } else if (mood === 'idle') {
                // Clear speech box when going idle
                clearSpeechBox();
            }
        }

        // Update speech text
        function updateSpeech(text) {
            const speechElement = document.getElementById('speechText');
            speechElement.style.animation = 'none';
            setTimeout(() => {
                speechElement.textContent = text;
                speechElement.style.animation = 'fadeIn 0.5s ease-in';
            }, 10);
        }

        // Terminal typing animation
        let typingInterval = null;

        function typeText(text, speed = 100) {
            const speechElement = document.getElementById('speechText');
            
            console.log(`⌨️  typeText() called with: "${text}", speed: ${speed}ms`);
            console.log(`   Speech element found:`, speechElement ? 'YES' : 'NO');
            
            // Clear any existing typing animation
            if (typingInterval) {
                console.log(`   Clearing existing typing interval`);
                clearInterval(typingInterval);
                typingInterval = null;
            }

            // Clear the text box
            speechElement.textContent = '';
            console.log(`   Cleared text box, starting to type...`);
            
            let index = 0;
            
            typingInterval = setInterval(() => {
                if (index < text.length) {
                    speechElement.textContent += text[index];
                    console.log(`   Typed character ${index + 1}/${text.length}: "${text[index]}" - Current text: "${speechElement.textContent}"`);
                    index++;
                } else {
                    clearInterval(typingInterval);
                    typingInterval = null;
                    console.log(`✅ Finished typing complete text: "${speechElement.textContent}"`);
                }
            }, speed);
        }

        function clearSpeechBox() {
            const speechElement = document.getElementById('speechText');
            
            console.log(`🧹 clearSpeechBox() called`);
            
            // Stop any typing animation
            if (typingInterval) {
                clearInterval(typingInterval);
                typingInterval = null;
                console.log(`   Stopped typing animation`);
            }
            
            // Clear the text
            speechElement.textContent = '';
            console.log(`   Text cleared`);
        }

        // API integration - call this from your Python backend
        function updateFromBackend(data) {
            if (data.mood) {
                changeMood(data.mood);
            }
            if (data.response) {
                // Use typing animation if specified, otherwise instant update
                if (data.typing === true) {
                    const speed = data.typing_speed || 100; // Default 100ms per char
                    typeText(data.response, speed);
                } else {
                    updateSpeech(data.response);
                }
            }
            if (data.clear_response === true) {
                clearSpeechBox();
            }
        }

        const ws = new WebSocket('ws://localhost:8765');

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateFromBackend(data);
        };

        ws.onopen = () => console.log("✅ Connected to Python backend");
        ws.onclose = () => console.log("❌ Backend disconnected");


        // TEST MODE: Auto-toggle between idle and responding every 5 seconds
        let testMode = true;
        let isResponding = false;

        function toggleResponse() {
            if (testMode) {
                isResponding = !isResponding;
                const mood = isResponding ? 'responding' : 'idle';
                console.log(`\n⏰ [TEST] Timer triggered - Switching to: ${mood.toUpperCase()}`);
                changeMood(mood);
            }
        }

        // Run test every 5 seconds
        //const testInterval = setInterval(toggleResponse, 5000);
        //console.log('⏱️  Test interval started (every 5 seconds)');

        // Toggle test mode on click of cat display
        document.querySelector('.cat-display').addEventListener('click', () => {
            testMode = !testMode;
            console.log('\n🖱️  Clicked! Test mode:', testMode ? 'ON (auto-toggling)' : 'OFF');
            if (!testMode) {
                changeMood('idle'); // Return to idle when test mode off
            }
        });
    </script>
</body>
</html>
"""

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(FRONTEND_HTML.encode('utf-8'))

def start_http_server():
    server = HTTPServer(("0.0.0.0", HTTP_PORT), MyHandler)
    print(f"🌐 UI → http://localhost:{HTTP_PORT}")
    server.serve_forever()


# ---------------------------- CONFIG ----------------------------
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise ValueError("Set ELEVENLABS_API_KEY environment variable!")

AGENT_ID = "agent_1601khf3r1jfff2saez29f6frfny"  # your agent ID
VOICE_ID = "XdflFrQO8wbGpWMNZHFr"                 # your TTS voice ID

RECORD_SECONDS = 5
CAT_SOUNDS_FOLDER = "cat_sounds"
WS_PORT = 8765
HTTP_PORT = 8000

connected_clients = set()

# ---------------------------- AUDIO DEVICE ----------------------------
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0 and d["max_output_channels"] > 0:
        sd.default.device = (i, i)
        print("Using audio device:", d["name"])
        DEFAULT_SR = int(d['default_samplerate'])
        break
else:
    raise RuntimeError("No suitable input/output device found")

# ---------------------------- AUDIO HELPERS ----------------------------
def resample_audio(audio, orig_sr, target_sr):
    if orig_sr == target_sr:
        return audio.astype(np.float32)
    duration = len(audio) / orig_sr
    new_length = int(duration * target_sr)
    if audio.ndim == 1:
        resampled = np.interp(np.linspace(0, len(audio)-1, new_length), np.arange(len(audio)), audio)
    else:
        channels = [np.interp(np.linspace(0, len(audio)-1, new_length), np.arange(len(audio)), audio[:, ch])
                    for ch in range(audio.shape[1])]
        resampled = np.stack(channels, axis=1)
    return resampled.astype(np.float32)

def record_audio(seconds, samplerate):
    print(f"Recording for {seconds} seconds at {samplerate} Hz...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

def speech_to_text(audio_np, samplerate):
    wav_file = "temp.wav"
    sf.write(wav_file, audio_np, samplerate)
    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": API_KEY}
    files = {"file": ("temp.wav", open(wav_file, "rb"), "audio/wav")}
    data = {"model_id": "scribe_v2"}
    r = requests.post(url, headers=headers, files=files, data=data)
    if r.status_code != 200:
        print("STT failed:", r.text)
        return ""
    return r.json().get("text", "")

def play_audio(audio_data, sr):
    audio_data = resample_audio(audio_data, sr, DEFAULT_SR)
    audio_data = audio_data.astype(np.float32)
    audio_data = audio_data / np.max(np.abs(audio_data))
    sd.play(audio_data, DEFAULT_SR)
    sd.wait()

def play_audio_dont_wait(audio_data, sr):
    audio_data = resample_audio(audio_data, sr, DEFAULT_SR)
    audio_data = audio_data.astype(np.float32)
    audio_data = audio_data / np.max(np.abs(audio_data))
    sd.play(audio_data, DEFAULT_SR)

def get_speech_from_elevenlabs(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"text": text, "model_id": "eleven_monolingual_v1"}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("TTS failed:", r.text)
        return None, None
    data, sr = sf.read(BytesIO(r.content), dtype="float32")
    return data, sr

def get_amplitude_envelope(data, sr, fps=30):
    chunk_size = sr // fps
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
    num_chunks = len(data) // chunk_size
    truncated_data = data[:num_chunks * chunk_size]
    chunks = truncated_data.reshape(num_chunks, chunk_size)
    rms_values = np.sqrt(np.mean(chunks**2, axis=1))
    max_rms = np.max(rms_values)
    return rms_values / max_rms if max_rms > 0 else rms_values

def play_cat_sound():
    cat_files = glob.glob(os.path.join(CAT_SOUNDS_FOLDER, "*.wav"))
    if not cat_files:
        return
    cat_file = random.choice(cat_files)
    data, sr = sf.read(cat_file, dtype="float32")
    play_audio(data, sr)

def play_cat_sound_and_move_motor(data, sr):
    play_cat_sound()
    amplitudes = get_amplitude_envelope(data, sr, fps=30)
    delay_between_frames = 1.0 / 30
    play_audio_dont_wait(data, sr)
    for amp in amplitudes:
        start_time = time.time()
        if amp > 0.1:
            speed = int(amp * 100)
            motorA_forward(speed=speed)
            motorB_forward(speed=speed)
        else:
            stop_motors()
        elapsed = time.time() - start_time
        time.sleep(max(0, delay_between_frames - elapsed))
    stop_motors()
    sd.wait()
    play_cat_sound()

def agent_reply(user_text):
    url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}/simulate-conversation"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "simulation_specification": {
            "simulated_user_config": {"first_message": user_text, "language": "en"},
            "agent_config": {"persona": "You are a toxic cat assistant...", "llm_override": "Respond in toxic cat style"}
        },
        "new_turns_limit": 1
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("Agent call failed:", r.text)
        return ""
    turns = r.json().get("simulated_conversation", [])
    for turn in turns:
        if turn.get("role") == "agent":
            return turn.get("message", "").replace("[sarcastic]", "").strip()
    return ""

# ---------------------------- WEBSOCKET ----------------------------
async def ws_handler(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def send_ui_update(data):
    if connected_clients:
        msg = json.dumps(data)
        await asyncio.gather(*(ws.send(msg) for ws in connected_clients))

# ---------------------------- VOICE LOOP ----------------------------
async def voice_loop():
    print("\nVoice agent ready! Speak into your mic.\n")
    try:
        while True:
            input("Press Enter to record your message...")
            await send_ui_update({"mood": "responding", "clear_response": True})
            audio_np = record_audio(RECORD_SECONDS, DEFAULT_SR)
            user_text = speech_to_text(audio_np, DEFAULT_SR)
            if not user_text:
                continue
            reply_text = agent_reply(user_text)
            if not reply_text:
                continue
            await send_ui_update({"response": reply_text, "typing": True, "typing_speed": 40})
            data, sr = get_speech_from_elevenlabs(reply_text)
            if data is not None:
                play_cat_sound_and_move_motor(data, sr)
            await send_ui_update({"mood": "idle"})
    except KeyboardInterrupt:
        cleanup_motors()

# ---------------------------- MAIN ----------------------------
async def main():
    # Run HTTP server in separate thread
    Thread(target=start_http_server, daemon=True).start()

    # Start WebSocket server
    await websockets.serve(ws_handler, "ws://localhost:8765", WS_PORT)
    print(f"🌐 WebSocket server running on ws://localhost:{WS_PORT}")

    # Start voice loop
    await voice_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Exiting and cleaning up motors...")
        cleanup_motors()
