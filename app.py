import time
from datetime import datetime
import json

from flask import Flask, render_template, request, send_file, jsonify
import os
import tempfile
import subprocess
from pathlib import Path
# Add this near the top of the file after imports
from threading import Lock
counter_lock = Lock()

def list_available_voices():
    voices = []
    for model_path in PIPER_MODELS_DIR.glob('**/*.onnx'):
        config_path = model_path.with_suffix('.onnx.json')
        if config_path.exists():
            voice_id = model_path.stem
            language, name, quality = model_path.parts[-4:-1]
            voices.append({
                'id': voice_id,
                'language': language,
                'name': name,
                'quality': quality,
                'model': str(model_path),
                'config': str(config_path)
            })
    return voices

# Create a variable to track last cleanup
last_cleanup = datetime.now()

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Configure base paths
PIPER_MODELS_DIR = Path('piper_models')
TEMP_DIR = Path(tempfile.gettempdir()) / 'piper_tts'
TEMP_DIR.mkdir(exist_ok=True)

def init_app(app):
    """Initialize the application"""
    try:
        # Clean old temp files
        for f in TEMP_DIR.glob('*.wav'):
            if f.stat().st_mtime < (time.time() - 3600):  # Older than 1 hour
                f.unlink()
    except Exception as e:
        app.logger.error(f"Cleanup error: {str(e)}")

@app.before_request
def cleanup_temp_files():
    """Periodically clean up temp files"""
    global last_cleanup
    
    # Only run cleanup once per hour
    if (datetime.now() - last_cleanup).total_seconds() >= 3600:
        try:
            # Clean old temp files
            for f in TEMP_DIR.glob('*.wav'):
                if f.stat().st_mtime < (time.time() - 3600):  # Older than 1 hour
                    f.unlink()
            last_cleanup = datetime.now()
        except Exception as e:
            app.logger.error(f"Cleanup error: {str(e)}")

class TTSError(Exception):
    """Custom exception for TTS processing errors"""
    pass

def validate_voice_paths(voice_id: str) -> tuple[Path, Path]:
    """
    Validate and normalize voice model and config paths
    Returns tuple of (model_path, config_path) as Path objects
    Raises TTSError if validation fails
    """
    voices = list_available_voices()
    selected_voice = next((voice for voice in voices if voice['id'] == voice_id), None)
    if not selected_voice:
        raise TTSError("Invalid voice ID")

    model_path = Path(selected_voice['model'])
    config_path = Path(selected_voice['config'])

    if not model_path.exists():
        raise TTSError(f"Model file not found: {model_path}")
    if not config_path.exists():
        raise TTSError(f"Config file not found: {config_path}")

    return model_path, config_path

def synthesize_text(text: str, model_path: Path, config_path: Path) -> Path:
    """
    Synthesize text to speech using Piper
    Returns path to output WAV file
    Raises TTSError if synthesis fails
    """
    if not text or not isinstance(text, str):
        raise TTSError("Invalid text input")

    # Create temp output file
    output_path = TEMP_DIR / f"{hash(text)}.wav"
    
    # Build piper command
    cmd = [
        str(Path(__file__).parent / 'piper' / 'piper'),
        '--model', str(model_path),
        '--config', str(config_path), 
        '--output_file', str(output_path)
    ]

    try:
        # Run piper process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send text and get output
        stdout, stderr = process.communicate(input=text)

        if process.returncode != 0:
            raise TTSError(f"Synthesis failed: {stderr}")
            
        # Verify output file was created
        if not output_path.exists():
            raise TTSError("Output file was not created")

        return output_path

    except FileNotFoundError:
        raise TTSError("Piper executable not found in PATH")
    except subprocess.TimeoutExpired:
        process.kill()
        raise TTSError("Synthesis timed out")
    except Exception as e:
        if process and process.poll() is None:
            process.kill()
        raise TTSError(f"Synthesis error: {str(e)}")
    finally:
        if process and process.poll() is None:
            process.kill()

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/voices', methods=['GET'])
def get_voices():
    """Return available voices"""
    try:
        voices = list_available_voices()
        return jsonify(voices)
    except Exception as e:
        app.logger.error(f"Error fetching voices: {str(e)}")
        return jsonify({'error': "Internal server error"}), 500

@app.route('/generation-count', methods=['GET'])
def get_generation_count():
    try:
        with open('db.json', 'r') as f:
            db = json.load(f)
            return jsonify({'count': db.get('generation_count', 0)})
    except FileNotFoundError:
        # Initialize db.json if it doesn't exist
        with open('db.json', 'w') as f:
            json.dump({'generation_count': 0}, f)
        return jsonify({'count': 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Handle TTS synthesis requests"""
    try:
        # Increment generation counter with thread safety
        with counter_lock:
            try:
                with open('db.json', 'r+') as f:
                    db = json.load(f)
                    db['generation_count'] = db.get('generation_count', 0) + 1
                    f.seek(0)
                    json.dump(db, f)
                    f.truncate()
            except FileNotFoundError:
                # Initialize db.json if it doesn't exist
                with open('db.json', 'w') as f:
                    json.dump({'generation_count': 1}, f)

        # Get request data
        data = request.get_json()
        if not data:
            raise TTSError("Missing request data")

        # Get and validate text
        text = data.get('text', '').strip()
        if not text:
            raise TTSError("No text provided")

        # Get and validate voice ID
        voice_id = data.get('voiceId')
        if not voice_id:
            raise TTSError("No voice ID provided")

        # Validate voice paths
        model_path, config_path = validate_voice_paths(voice_id)

        # Synthesize speech
        output_path = synthesize_text(text, model_path, config_path)

        # Return audio file
        return send_file(
            output_path,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='speech.wav'
        )

    except TTSError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Synthesis error: {str(e)}")
        return jsonify({'error': "Internal server error"}), 500

if __name__ == '__main__':
    # Initialize the app before running
    init_app(app)
    app.run(debug=True)
