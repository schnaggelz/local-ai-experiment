# Hailo Speech Recognition on Raspberry Pi 5

## Prerequisites

Install required system package:

```sh
sudo apt update && sudo apt-get install -y portaudio19-dev
```

Get and install Hailo packages (for me a code patch was required to get the kernel module installed):

```sh
sudo apt install ./hailort-pcie-driver_5.3.0_all.deb
sudo apt install ./hailort_5.3.0_arm64.deb
sudo apt install ./hailo_gen_ai_model_zoo_5.3.0_arm64.deb
```

In separate venv

```sh
python3 -m venv .venv-hailo-sdk
source .venv-hailo-sdk/bin/activate

pip install ./hailort-5.3.0-cp313-cp313-linux_aarch64.whl
pip3 install -r hailo/requirements.txt
```

## Voice Control

Listens on the microphone, runs Whisper on the Hailo NPU, and dispatches matched utterances as Home Assistant light commands.

### Structure

```
hailo/speech_recognition/
  common/                      shared modules
    speech_capture.py          WebRTC VAD-based audio capture
    hailo_decoder.py           Whisper inference via HailoRT
    device_discovery.py        PyAudio device enumeration
  config/                      shared YAML configuration
    command_patterns.yaml      spoken phrases  →  turn_on / turn_off / toggle
    entity_patterns.yaml       spoken room names  →  HA entity IDs
  listen_transcribe/           app: transcribe and print to stdout
    listen_transcribe.py
  voice_control/               app: transcribe and dispatch HA commands
    voice_control.py
    command_translator.py
    home_assistant.py
```

### Quick start

```bash
cd hailo/speech_recognition
export HA_TOKEN="<your-long-lived-token>"

# Transcribe only
python3 -m listen_transcribe.listen_transcribe \
    --hef ../../models/whisper_base.hef \
    --input-device 1 \
    --language de

# Voice → Home Assistant
python3 -m voice_control.voice_control \
    --hef ../../models/whisper_base.hef \
    --input-device 1 \
    --language de
```

Say the wake word (*maus* by default) followed by a room name and command, e.g. *„Maus, Wohnzimmer an"*. Use `--no-wake-word` to process every utterance directly.

### Configuration

Edit the YAML files in `config/` — no code changes needed:

**`config/entity_patterns.yaml`** — map spoken names to HA entity IDs:
```yaml
- pattern: '\b(wohnzimmer|wohn|living room)\b'
  entity_id: light.living_room
```

**`config/command_patterns.yaml`** — map spoken phrases to actions:
```yaml
- pattern: '\b(an|ein|einschalten|turn on)\b'
  action: turn_on
```

### CLI reference

| Flag | Default | Description |
|---|---|---|
| `--hef` | *(required)* | Path to `whisper_base.hef` |
| `--input-device` | auto | PyAudio device index (`--list-devices` to enumerate) |
| `--language` | `de` | Whisper language code |
| `--wake-word` | `maus` | Keyword to activate command mode |
| `--no-wake-word` | off | Process every utterance without a wake word |
| `--active-time-window` | `10` | Seconds to stay active after the wake word |
| `--vad-mode` | `2` | WebRTC VAD aggressiveness 0–3 |
| `--timeout` | `5.0` | Max capture length per utterance (seconds) |
| `--ha-url` | `http://192.168.242.21:8123` | Home Assistant base URL (`voice_control` only) |
| `--ha-token` | `$HA_TOKEN` | Long-lived access token (`voice_control` only) |
| `--log-level` | `INFO` | Logging verbosity |
