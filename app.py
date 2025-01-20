from flask import Flask, render_template, request, send_file, jsonify
import os
import tempfile
import subprocess

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.json
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_file = temp_file.name

        # Run piper with the input text
        piper_command = [
            'piper',
            '--model', './piper/etc/test_voice.onnx',
            '--output_file', output_file
        ]
        
        try:
            process = subprocess.Popen(
                piper_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=text)

            if process.returncode != 0:
                return jsonify({'error': stderr}), 500
        except FileNotFoundError:
            return jsonify({'error': 'Piper not found. Make sure it is installed and in your PATH'}), 500

        return send_file(output_file, mimetype='audio/wav')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
