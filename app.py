from flask import Flask, request, jsonify
import threading
import time
import subprocess
import os
import logging

# Optional imports with graceful fallbacks
try:
    import whisper
    WHISPER_AVAILABLE = True
    # Load Whisper model only if available
    try:
        model = whisper.load_model("base")
    except Exception as e:
        logging.warning(f"Failed to load Whisper model: {e}")
        WHISPER_AVAILABLE = False
        model = None
except ImportError:
    WHISPER_AVAILABLE = False
    model = None

try:
    import openai
    OPENAI_AVAILABLE = True
    # OpenAI API key from environment variable
    openai.api_key = os.getenv("OPENAI_API_KEY", "")
    if not openai.api_key:
        logging.warning("OPENAI_API_KEY environment variable not set")
        OPENAI_AVAILABLE = False
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to capture screen content
def capture_screen():
    if not PIL_AVAILABLE:
        logging.warning("PIL not available, screen capture disabled")
        return
    
    while True:
        try:
            # Check if we're in a headless environment
            screenshot = ImageGrab.grab()
            screenshot.save("screenshot.png")
            logging.info("Screenshot captured successfully")
        except Exception as e:
            logging.warning(f"Screen capture failed: {e}")
            # In headless environment, just log and continue
            pass
        time.sleep(5)  # Capture every 5 seconds

# Endpoint for voice recognition
@app.route('/recognize', methods=['POST'])
def recognize():
    if not WHISPER_AVAILABLE or model is None:
        return jsonify({"error": "Whisper model not available"}), 503
    
    if 'file' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        result = model.transcribe(audio_file)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        return jsonify({"error": "Transcription failed"}), 500

# Endpoint for executing system commands (restricted for security)
@app.route('/command', methods=['POST'])
def command():
    data = request.json
    if not data or 'command' not in data:
        return jsonify({"error": "No command provided"}), 400
    
    command = data.get('command', '').strip()
    if not command:
        return jsonify({"error": "Empty command"}), 400
    
    # Security: Only allow safe commands
    allowed_commands = ['echo', 'ls', 'pwd', 'date', 'whoami', 'uname']
    command_parts = command.split()
    if not command_parts or command_parts[0] not in allowed_commands:
        return jsonify({"error": f"Command '{command_parts[0] if command_parts else ''}' not allowed. Allowed: {allowed_commands}"}), 403
    
    try:
        # Execute the command with timeout and restrictions
        result = subprocess.run(command_parts, capture_output=True, text=True, timeout=10)
        return jsonify({
            "status": "success", 
            "output": result.stdout, 
            "error": result.stderr,
            "return_code": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timed out"}), 408
    except Exception as e:
        logging.error(f"Command execution failed: {e}")
        return jsonify({"error": "Command execution failed"}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "features": {
            "whisper": WHISPER_AVAILABLE,
            "openai": OPENAI_AVAILABLE,
            "pil": PIL_AVAILABLE
        }
    })

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "Voice Assistant API",
        "endpoints": ["/health", "/recognize", "/command"],
        "features": {
            "whisper": WHISPER_AVAILABLE,
            "openai": OPENAI_AVAILABLE,
            "pil": PIL_AVAILABLE
        }
    })

# Start screen capture in a separate thread (only if PIL is available)
if PIL_AVAILABLE:
    threading.Thread(target=capture_screen, daemon=True).start()
    logging.info("Screen capture thread started")
else:
    logging.info("Screen capture disabled (PIL not available)")

if __name__ == '__main__':
    logging.info("Starting Voice Assistant API")
    app.run(host='0.0.0.0', port=5000, debug=True)  # Fixed port to match Dockerfile
