# NVIDIA Jetson AGX Xavier Reflash via Docker

This directory documents the safest repeatable path for reflashing a Jetson AGX Xavier from Linux without installing SDK Manager directly on the host. The flow uses NVIDIA's official `sdkmanager` Docker image in CLI mode, a Compose file for the fixed container settings and command templates, and a small wrapper script for the variable environment and service selection.

Files in this directory:

- `docker-compose.yml` - Static container definition plus direct Compose services for query, detection, download-only, and flash flows.
- `.env.example` - Sample environment file for direct Compose usage.
- `sdkmanager-docker.sh` - Thin wrapper that exports the environment, selects a Compose service, and runs it.

## What this does

The Docker image handles the same flash flow as native SDK Manager, but NVIDIA documents a few constraints that matter here:

- The Docker image is CLI-only.
- Flashing requires privileged access plus USB passthrough.
- The host still needs `qemu-user-static` and binfmt support enabled, or the rootfs stage can fail with `dpkg: Exec format error`.

## 1. Prepare the Linux host

Install the host-side binfmt helpers before you try to flash.

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

The last command should print a registered `qemu-aarch64` entry instead of failing.

## 2. Download and load NVIDIA's SDK Manager Docker image

Download the matching SDK Manager Docker tarball from NVIDIA:

- https://developer.nvidia.com/nvidia-sdk-manager
- https://docs.nvidia.com/sdk-manager/docker-containers/index.html

Then load it locally:

```sh
docker load -i ./sdkmanager-[version].[build]-ubuntu2004_docker.tar.gz
docker tag sdkmanager:[version].[build] sdkmanager:latest
```

The wrapper script and Compose file default to `sdkmanager:latest`. If you keep a different tag, export `SDKMANAGER_IMAGE` before running it.

If you want to run Compose directly without the wrapper, work from this directory so `.env` is picked up cleanly:

```sh
cd /home/timon/Develop/local-ai-experiments/jetson-agx
cp .env.example .env
mkdir -p .sdkm/downloads .sdkm/nvidia_sdk
```

Then edit `.env` for your machine, especially:

- `SDKM_MEDIA_DIR`
- `JETPACK_VERSION`
- `JETSON_TARGET`
- `SDKM_USB_PORT` if more than one Jetson is attached

## 3. Put the Xavier into force recovery mode

For a dev kit, the usual sequence is:

1. Power the board off.
2. Hold the recovery button.
3. Tap the power button.
4. Release the recovery button after the board powers on.
5. Connect the host to the Jetson's flashing USB port.

On the host, verify the device appears on USB before starting a flash:

```sh
lsusb | grep -i nvidia
```

## 4. Discover the correct JetPack version and target ID

Do not guess the target ID. Ask SDK Manager for the exact values it supports for your account and SDK Manager version.

Show available Jetson options:

```sh
cd /home/timon/Develop/local-ai-experiments
./jetson-agx/sdkmanager-docker.sh query --product Jetson --show-all-versions
```

Direct Compose equivalent:

```sh
cd /home/timon/Develop/local-ai-experiments/jetson-agx
SDKM_EXTRA_ARGS='--product Jetson --show-all-versions' docker compose run --rm sdkmanager-query
```

List connected Jetson devices and USB port IDs:

```sh
./jetson-agx/sdkmanager-docker.sh list-connected
```

Direct Compose equivalent:

```sh
cd /home/timon/Develop/local-ai-experiments/jetson-agx
docker compose run --rm sdkmanager-list-connected
```

For AGX Xavier hardware, expect to use a JetPack 5.x release in most cases. If your query output does not show the release you need, rerun with archived versions enabled:

```sh
SDKM_ARCHIVED_VERSIONS=1 ./jetson-agx/sdkmanager-docker.sh query --product Jetson --show-all-versions
```

Write down:

- The JetPack version you want, for example `5.1.4`.
- The exact target ID reported by SDK Manager for your board, for example a Xavier AGX target string.
- The USB port ID if more than one Jetson is connected.

## 5. Flash the board

If you want to prefetch the artifacts first and flash later, run download-only:

```sh
cd /home/timon/Develop/local-ai-experiments
JETPACK_VERSION=5.1.4 \
JETSON_TARGET=JETSON_AGX_XAVIER_TARGETS \
./jetson-agx/sdkmanager-docker.sh download-only
```

Direct Compose equivalent:

```sh
cd /home/timon/Develop/local-ai-experiments/jetson-agx
docker compose run --rm sdkmanager-download-only
```

Then flash the board once the downloads are already present.

Run the wrapper with the JetPack version and target ID you discovered above:

```sh
cd /home/timon/Develop/local-ai-experiments
JETPACK_VERSION=5.1.4 \
JETSON_TARGET=JETSON_AGX_XAVIER_TARGETS \
./jetson-agx/sdkmanager-docker.sh flash
```

If SDK Manager only exposes the Xavier release through archived listings, add:

```sh
SDKM_ARCHIVED_VERSIONS=1
```

If multiple Jetsons are attached, pin the USB path reported by `list-connected`:

```sh
cd /home/timon/Develop/local-ai-experiments
JETPACK_VERSION=5.1.4 \
JETSON_TARGET=JETSON_AGX_XAVIER_TARGETS \
SDKM_USB_PORT=1-2.4 \
./jetson-agx/sdkmanager-docker.sh flash
```

The first run will prompt for NVIDIA login in the terminal flow. Downloads and generated images persist under `jetson-agx/.sdkm/`, so repeat flashes do not have to start from zero.

Direct Compose equivalent:

```sh
cd /home/timon/Develop/local-ai-experiments/jetson-agx
docker compose run --rm sdkmanager-flash
```

## 6. Re-run a flash without rebuilding state

The wrapper persists these directories on the host:

- `jetson-agx/.sdkm/downloads`
- `jetson-agx/.sdkm/nvidia_sdk`

That means you can re-run the same flash command later and reuse the previously downloaded artifacts.

## Common failure points

- `dpkg: Exec format error`: host binfmt support is missing. Reinstall `qemu-user-static`, enable binfmt, and retry.
- Jetson not detected: the board is not actually in force recovery mode, the wrong USB cable/port is in use, or another USB device mapping issue exists on the host.
- Flash hangs while talking to the target over USB networking: keep `SDKM_DOCKER_NETWORK=host` or leave the default alone.
- Desired JetPack version missing: query with `--show-all-versions` and set `SDKM_ARCHIVED_VERSIONS=1`.
- External NVMe or other external-storage flashing: NVIDIA notes Docker flashing support is not complete for every Jetson external-storage path. Internal eMMC flashing is the safer baseline.

## Useful commands

Show help for the wrapper:

```sh
./jetson-agx/sdkmanager-docker.sh --help
```

Use a non-default SDK Manager image tag:

```sh
SDKMANAGER_IMAGE=sdkmanager:2.4.0 ./jetson-agx/sdkmanager-docker.sh query --product Jetson
```

Inspect the final Compose configuration the wrapper will use:

```sh
cd /home/timon/Develop/local-ai-experiments
SDKM_DOWNLOADS_DIR=$PWD/jetson-agx/.sdkm/downloads \
SDKM_TARGET_IMAGE_DIR=$PWD/jetson-agx/.sdkm/nvidia_sdk \
SDKM_MEDIA_DIR=/media/$USER \
docker compose -f jetson-agx/docker-compose.yml config
```

List the available direct Compose services:

```sh
cd /home/timon/Develop/local-ai-experiments/jetson-agx
docker compose config --services
```
