import time
from datetime import datetime
import json
from collections import deque
from threading import Lock

from flask import Flask, render_template, request, send_file, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import tempfile
import subprocess
from pathlib import Path
from threading import Lock

# Thread-safe locks and queues
counter_lock = Lock()
queue_lock = Lock()
request_queue = deque()
queue_positions = {}



def llist_available_voices_filename_origin():
    """
    Lists available voices by scanning PIPER_MODELS_DIR.
    Origin is determined by keywords in the filename.
    Speed is still derived from the quality folder name.
    Voice name is extracted and simplified from the filename.
    "Unknown" origin/speed are removed from display name if possible.
    """
    voices = []
    for model_path in PIPER_MODELS_DIR.glob('**/*.onnx'):
        try:
            config_path = model_path.with_suffix('.onnx.json')
            if not config_path.exists():
                print(f"Warning: Config file not found for model: {model_path}. Skipping.")
                continue

            voice_id = model_path.stem
            path_parts = model_path.parts

            if len(path_parts) >= 5:
                language = path_parts[-4]
                region_code = path_parts[-3]
                name_folder = path_parts[-2]
                quality = path_parts[-1]

                # --- Determine origin from filename keywords ---
                filename = model_path.name
                origin_name = "unknown"

                if "en_US" in filename:
                    origin_name = "american"
                elif "en_GB" in filename:
                    origin_name = "british"
                elif "en_AU" in filename:
                    origin_name = "australian"
                elif language == 'de':
                    origin_name = "german"
                elif language == 'es':
                    origin_name = "spanish"
                elif language == 'fr':
                    origin_name = "french"
                elif language == 'it':
                    origin_name = "italian"
                elif language == 'ja':
                    origin_name = "japanese"
                elif language == 'ko':
                    origin_name = "korean"
                elif language == 'nl':
                    origin_name = "dutch"
                elif language == 'pl':
                    origin_name = "polish"
                elif language == 'pt':
                    origin_name = "portuguese"
                elif language == 'ru':
                    origin_name = "russian"
                elif language == 'zh':
                    origin_name = "chinese"
                else:
                    origin_name = language

                # --- Extract and simplify voice name from filename ---
                actual_name = filename
                prefixes_to_remove = ["en_GB-", "en_US-", "en_AU-", "de-", "es-", "fr-", "it-", "ja-", "ko-", "nl-", "pl-", "pt-", "ru-", "zh-"]
                suffixes_to_remove = ["-low", "-medium", "-high", ".onnx", "-low", "-medium", "-high"] # Added quality suffixes here

                for prefix in prefixes_to_remove:
                    if actual_name.startswith(prefix):
                        actual_name = actual_name[len(prefix):]
                        break

                for suffix in suffixes_to_remove:
                    if actual_name.endswith(suffix):
                        actual_name = actual_name[:-len(suffix)]

                actual_name = actual_name.replace("_", " ").strip()
                actual_name = actual_name.capitalize()

                # --- Speed mapping and formatting ---
                speed_map = {
                    'high': 'slow',
                    'medium': 'medium',
                    'low': 'fast'
                }
                speed_raw = quality
                speed = speed_map.get(quality, 'unknown')

                speed_display = speed.capitalize()
                if speed_display != "Unknown":
                    speed_display = f" - {speed_display}"

                # --- Origin formatting ---
                origin_display = origin_name.capitalize()
                if origin_display != "Unknown":
                    origin_display = f" - {origin_display}"

                # --- Construct display name with conditional parts and spaces ---
                if origin_name == "unknown" and speed == "unknown":
                    display_name = f"{actual_name}"
                elif origin_name == "unknown":
                    display_name = f"{actual_name}{speed_display}"
                elif speed == "unknown":
                    display_name = f"{actual_name}{origin_display}"
                else:
                    display_name = f"{actual_name}{origin_display}{speed_display}"


                voices.append({
                    'id': voice_id,
                    'language': language,
                    'region_code': region_code,
                    'name': name_folder,
                    'quality': quality,
                    'quality_raw': speed_raw,
                    'speed': speed,
                    'display_name': display_name,
                    'model': str(model_path),
                    'config': str(config_path)
                })
            else:
                print(f"Warning: Unexpected path structure for model: {model_path}. Skipping.")

        except Exception as e:
            print(f"Error processing voice model {model_path}: {e}")

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
    voices = llist_available_voices_filename_origin()
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
        voices = llist_available_voices_filename_origin()
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

@app.route('/queue-position', methods=['GET'])
def get_queue_position():
    """Get current queue position for client"""
    client_ip = get_remote_address()
    with queue_lock:
        position = queue_positions.get(client_ip, 0)
        return jsonify({'position': position})

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Handle TTS synthesis requests with rate limiting and queue system"""
    client_ip = get_remote_address()
    
    # Add to queue
    with queue_lock:
        request_queue.append(client_ip)
        queue_positions[client_ip] = len(request_queue)
    
    try:
        # Wait for turn
        while True:
            with queue_lock:
                if request_queue[0] == client_ip:
                    break
            time.sleep(1)

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
    finally:
        # Remove from queue
        with queue_lock:
            if client_ip in queue_positions:
                request_queue.remove(client_ip)
                del queue_positions[client_ip]
                # Update positions for remaining clients
                for idx, ip in enumerate(request_queue):
                    queue_positions[ip] = idx + 1

if __name__ == '__main__':
    # Initialize the app before running
    init_app(app)
    app.run(debug=True, port=5001)
