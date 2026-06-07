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
S