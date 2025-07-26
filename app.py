from flask import Flask, request, jsonify
import whisper
import openai
import threading
import time
import subprocess
from PIL import ImageGrab

app = Flask(__name__)

# Load Whisper model
model = whisper.load_model("base")

# OpenAI API key
openai.api_key = "YOUR_OPENAI_API_KEY"

# Function to capture screen content
def capture_screen():
    while True:
        screenshot = ImageGrab.grab()
        screenshot.save("screenshot.png")
        time.sleep(5)  # Capture every 5 seconds

# Endpoint for voice recognition
@app.route('/recognize', methods=['POST'])
def recognize():
    audio_file = request.files['file']
    result = model.transcribe(audio_file)
    return jsonify(result)

# Endpoint for executing system commands
@app.route('/command', methods=['POST'])
def command():
    data = request.json
    command = data.get('command')
    try:
        # Execute the command using subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return jsonify({"status": "success", "output": result.stdout, "error": result.stderr})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Start screen capture in a separate thread
threading.Thread(target=capture_screen, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
