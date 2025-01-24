import os
import json

# Mapping dictionaries
LANGUAGE_MAP = {
    "en_GB": "English",
    "en_US": "English"
}

QUALITY_MAP = {
    "high": "slow",
    "medium": "medium", 
    "low": "fast"
}

GENDER_MAP = {
    "male": "Male",
    "female": "Female"
}

def format_display_name(path):
    """Generate display name from file path"""
    parts = path.split('/')
    # Path format: piper_models/en/en_GB/voice_name/quality/en_GB-voice_name-quality.onnx.json
    lang_code = parts[2]
    voice_name = parts[3].capitalize()
    quality = parts[4]
    gender = "Male" if "male" in path.lower() else "Female"
    
    language = LANGUAGE_MAP.get(lang_code, lang_code)
    region = "British" if lang_code == "en_GB" else "American"
    
    return f"{voice_name} - {language} - {region} {gender}"

def process_json_file(json_path):
    """Add/update display_name in JSON file"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Add/update display_name
    data['display_name'] = format_display_name(json_path)
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    base_dir = "piper_models"
    
    # Walk through all JSON files
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                process_json_file(json_path)
                print(f"Updated {json_path}")

if __name__ == "__main__":
    main()
