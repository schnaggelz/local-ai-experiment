# Hailo Speech Recognition on Raspberry Pi 5

## Prerequisites

Required system package:

```sh
sudo apt-get update && sudo apt-get install -y portaudio19-dev
```

In separate venv

```sh
python3 -m venv .venv-hailo-sdk
source .venv-hailo-sdk/bin/activate
pip3 install -r hailo/requirements.txt
```