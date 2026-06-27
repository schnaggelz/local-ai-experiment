# NVIDIA Jetson AGX Xavier Setup

## SDK Manager via Docker

This directory keeps only the pieces required to enter NVIDIA SDK Manager from Docker on a Linux host. After the container starts, use the normal interactive SDK Manager wizard to pick JetPack, detect the Xavier, and start the flash.

Files in this directory:

- `docker-compose.yml` - Static container definition with the required privileged mode, USB passthrough, host networking, and persistent download mounts.
- `.env.example` - Sample environment file for the Compose service.
- `sdkmanager-docker.sh` - Thin launcher for `docker compose run --rm sdkmanager`.

### Prepare the host

SDK Manager's Docker image still depends on host binfmt support. Without it, Jetson installs can fail with `dpkg: Exec format error`.

Arch Linux:

```sh
sudo pacman -Syu qemu-user-static qemu-user-static-binfmt
sudo systemctl restart systemd-binfmt.service
cat /proc/sys/fs/binfmt_misc/qemu-aarch64
```

Ubuntu or Debian:

```sh
sudo apt update
sudo apt install -y qemu-user-static binfmt-support
sudo update-binfmts --enable
cat /proc/sys/fs/binfmt_misc/qemu-aarch64
```

### Load the SDK Manager image

For Jetson AGX Xavier, use the Ubuntu 20.04 SDK Manager Docker image.

Download the tarball from NVIDIA, then load it locally:

```sh
docker load -i ./sdkmanager-[version].[build]-ubuntu2004_docker.tar.gz
docker tag sdkmanager:[version].[build] sdkmanager:latest
```

If you keep a different image tag, set `SDKMANAGER_IMAGE` in `.env` or export it before launching.

### Prepare local state

From this directory:

```sh
cd /home/timon/Develop/local-ai-experiments/jetson-agx
cp .env.example .env
mkdir -p .sdkm/downloads .sdkm/nvidia_sdk
```

Edit `.env` if needed. The main setting is `SDKM_MEDIA_DIR`, which should match your host media path.

### Put the Xavier into recovery mode

For a dev kit:

1. Power the board off.
2. Hold the recovery button.
3. Tap the power button.
4. Release the recovery button after the board powers on.
5. Connect the host to the Jetson flashing USB port.

Optional host check:

```sh
lsusb | grep -i nvidia
```

### Start SDK Manager

With the wrapper:

```sh
cd /home/timon/Develop/local-ai-experiments
./jetson-agx/sdkmanager-docker.sh
```

Direct Compose equivalent:

```sh
cd /home/timon/Develop/local-ai-experiments/jetson-agx
docker compose run --rm sdkmanager
```

Inside the wizard, select Jetson, choose the Xavier-compatible JetPack release, and continue through NVIDIA's normal interactive flow.

#### Notes

- The Docker image is CLI-only, so you interact through the terminal wizard.
- Downloads and generated artifacts persist under `jetson-agx/.sdkm/`.
- Host networking is enabled because SDK Manager may need it for Jetson USB device mode.

## Setup on Target

### Setup Docker environment

```sh
sudo apt update
sudo apt install -y docker.io nvidia-container-toolkit nvidia-container-runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
sudo systemctl restart docker
```

