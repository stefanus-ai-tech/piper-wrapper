# Piper Text-to-Speech

Piper is a fast, local neural text-to-speech system that sounds great and is optimized for the Raspberry Pi 4. This repository contains the source code for the Piper TTS system, including a web interface for synthesizing speech from text.

## Features

- Supports multiple languages and voices
- High-quality speech synthesis
- Optimized for Raspberry Pi 4
- Easy to use web interface

## Installation

### Prerequisites

- Python 3.6+
- Flask

### Clone the Repository

```sh
git clone https://github.com/stefanus-ai-tech/piper-wrapper
cd piper-tts
```

### Install the wrapper dependencies

```sh
python3 -m venv myenv
source myvenv/bin/activate
pip install -r requirements.txt
```

### Instal piper dependencies

```sh
cd piper/src/python_run
pip install -r requirements.txt
```


### Download the model

```sh
./download_piper_models.sh
```
