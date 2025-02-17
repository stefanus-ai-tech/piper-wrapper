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
cd piper-wrapper
```

### Install the wrapper dependencies

```sh
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### Instal piper dependencies

```sh
cd piper_repo/src/python_run
pip install -r requirements.txt
pip install cython>=0.29.0
pip install librosa>=0.9.2 
pip install numpy>=1.19.0 
pip install onnxruntime>=1.11.0
pip install pytorch-lightning==1.7.0 
pip install torch==1.11.0
pip install torchtext==0.12.0 
pip install torchvision==0.12.0
pip install torchaudio==0.11.0 
pip install torchmetrics==0.11.4
pip install piper-tts==1.2.0
```
If that still doesn't work, try installing with the --no-deps flag and then install dependencies separately:

```sh
pip install --no-deps piper-tts==1.2.0
```

To install piper_phonemize library
```sh
cd piper-phonemize
pip install .
```

### Install docker and docker compose

```sh
sudo apt update
sudo apt install build-essential
pip install --upgrade setuptools wheel
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo echo  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo apt install docker-compose
```


### Download the model

```sh
./download_piper_models.sh
```

### Build with docker
```sh
sudo docker-compose build
```
