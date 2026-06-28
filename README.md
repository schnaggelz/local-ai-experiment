# Local AI Experiments

Small experiments for running local AI services with Ubuntu Docker containers or Raspberry Pi 5.

## Raspberry Pi 5 Hailo Voice Control

Runs Whisper on a Hailo-8 NPU, wakes on a keyword, and controls Home Assistant lights by voice.

See [hailo/speech_recognition/README.md](hailo/speech_recognition/README.md) for setup and usage.


## Nvidia Jetson AGX Ollama Server

See [README](services/jetson-sdk/README.md) for setting up the AGX.

### Run Ollama Server

Run the standard ollama docker container, it already contains Jetpack support:

```sh
docker run -d --runtime nvidia \
 --name ollama \
 --network host \
 -e JETSON_JETPACK=5 \
 -e OLLAMA_MODELS=/models \
 -e OLLAMA_CONTEXT_LENGTH=32768 \
 -v /mnt/ssd/ollama:/models \
 ollama/ollama:latest
```
If you want the lightest-weight option, keep the `docker run` command and add `--restart unless-stopped`.

For the most reliable setup, run the container under systemd so it starts at boot and is managed like a normal service.

Create `/etc/systemd/system/ollama.service` with:

```ini
[Unit]
Description=Ollama on Jetson AGX Xavier
After=docker.service
Requires=docker.service

[Service]
Restart=unless-stopped
ExecStart=/usr/bin/docker run --rm --runtime nvidia \
	--name ollama \
	--network host \
	-e JETSON_JETPACK=5 \
	-e OLLAMA_MODELS=/models \
	-e OLLAMA_CONTEXT_LENGTH=32768 \
	-e OLLAMA_MAX_LOADED_MODELS=1 \
	-e OLLAMA_NUM_PARALLEL=1 \
	-v /mnt/ssd/ollama:/models \
	ollama/ollama:latest
ExecStop=/usr/bin/docker stop ollama

[Install]
WantedBy=multi-user.target
```

Then enable it:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now ollama.service
```

### Notes

Get logs with

```sh
docker logs ollama -f
```

Enter container with:

```sh
docker exec -it ollama /bin/bash
```

## ROCm Ollama Server

This variant builds a local Ollama image on top of Ubuntu 24.04, installs ROCm inside the container, and starts `ollama serve` directly through Compose.

### Files

- `services/ollama-rocm/Dockerfile` - Ubuntu-based image with ROCm and Ollama installed.
- `services/ollama-rocm/docker-compose.yml` - Compose service definition, GPU device passthrough, and runtime environment defaults.
- `services/ollama-rocm/.env` - Optional per-service Compose overrides for port and Ollama runtime settings.

### Requirements

- Docker with Compose support.
- A ROCm-capable AMD GPU with `/dev/kfd` and `/dev/dri` access.

### Quick Start

1. Change into `services/ollama-rocm`.
2. Optionally edit `.env` to override the exposed port or Ollama runtime defaults.
3. Start the service with Compose.
4. Pull or run models through the Ollama API or CLI once the container is up.

Example:

```bash
cd services/ollama-rocm
docker compose up -d
docker compose exec ollama-rocm ollama pull llama3.2
```

The server listens on port `11434` by default.

### Common Configuration

The Compose file exposes these environment variables:

- `OLLAMA_PORT`
- `OLLAMA_HOST`
- `OLLAMA_KEEP_ALIVE`
- `OLLAMA_CONTEXT_LENGTH`
- `OLLAMA_MAX_LOADED_MODELS`
- `OLLAMA_MAX_QUEUE`
- `OLLAMA_NUM_GPU`
- `OLLAMA_GPU_OVERHEAD`
- `OLLAMA_NUM_PARALLEL`
- `OLLAMA_KV_CACHE_TYPE`
- `OLLAMA_FLASH_ATTENTION`
- `OLLAMA_DEBUG`

Defaults are defined in `docker-compose.yml` and can be overridden in the service `.env` file or by exporting variables on the command line before running Compose.

### Notes

- The `./data` directory persists downloaded models across container restarts.
- `OLLAMA_KEEP_ALIVE=10m` keeps a recently used model warm without pinning it indefinitely.
- `OLLAMA_MAX_LOADED_MODELS=1` is a safer default for a single local ROCm GPU where VRAM is the main constraint.
- If you run Compose from outside `docker/services/ollama-rocm`, use `docker compose --env-file docker/services/ollama-rocm/.env -f docker/services/ollama-rocm/docker-compose.yml up -d` so the service-specific overrides are used consistently.

## ROCm llama.cpp Server

The main setup in this repo is a `llama.cpp` server container built for ROCm GPUs. It now builds a local image from the upstream `llama.cpp` sources and uses a small shell wrapper to pass through environment variables into the server process.

### Files

- `services/llama-cpp-rocm/Dockerfile` - Local ROCm build for `llama-server`.
- `services/llama-cpp-rocm/docker-compose.yml` - Compose service definition, GPU device passthrough, build settings, and default runtime settings.
- `services/llama-cpp-rocm/run-llama-server.sh` - Entrypoint script that converts environment variables into `llama-server` CLI flags.
- `services/ollama-rocm/.env` - Optional per-service Compose overrides for port and llama.cpp runtime settings.

### Requirements

- Docker with Compose support.
- A ROCm-capable AMD GPU with `/dev/kfd` and `/dev/dri` access.
- A GGUF model file mounted into the container.

### Quick start

1. Place or mount a model file under the local `models/` directory, or point `MODELS_DIR` elsewhere.
2. Set `MODEL` to the path of the model inside `/models`.
3. Optionally set `LLAMA_CPP_REF` if you want to pin a llama.cpp branch, tag, or commit-ish.
4. Optionally set `ROCM_DOCKER_ARCH` to control which AMD GPU architectures are compiled into the image.
5. Start the service from `services/llama-cpp-rocm`.

Example:

```bash
MODEL=~/.gguf/mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf docker compose up -d
```

The server listens on port `8080` by default.

### Common configuration

The Compose file already exposes a set of useful environment variables, including:

- `ROCM_DOCKER_ARCH`
- `LLAMA_PORT`
- `LLAMA_CTX_SIZE`
- `LLAMA_GPU_LAYERS`
- `LLAMA_N_CPU_MOE`
- `LLAMA_CPU_MOE`
- `LLAMA_FLASH_ATTN`
- `LLAMA_METRICS`
- `LLAMA_VERBOSE`

Most values have sensible defaults, but `MODEL` is required.

### Notes

- The wrapper script enables optional flags only when the matching environment variable is set.
- The container is configured for ROCm and may not work with non-ROCm images or GPUs without adjustment.

## PyTorch / ROCm ML Environment

Scripts for setting up a ROCm-based PyTorch environment, checking the local GPU/ML stack, and exporting models to ONNX.

See [pytorch/README.md](pytorch/README.md) for installation steps and usage.

