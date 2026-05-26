# Local AI Experiments

Small experiments for running local AI services with Docker.

## ROCm llama.cpp server

The main setup in this repo is a `llama.cpp` server container built for ROCm GPUs. It now builds a local image from the upstream `llama.cpp` sources and uses a small shell wrapper to pass through environment variables into the server process.

### Files

- `docker/services/llama-cpp-rocm/Dockerfile` - Local ROCm build for `llama-server`.
- `docker/services/llama-cpp-rocm/docker-compose.yml` - Compose service definition, GPU device passthrough, build settings, and default runtime settings.
- `docker/services/llama-cpp-rocm/run-llama-server.sh` - Entrypoint script that converts environment variables into `llama-server` CLI flags.

### Requirements

- Docker with Compose support.
- A ROCm-capable AMD GPU with `/dev/kfd` and `/dev/dri` access.
- A GGUF model file mounted into the container.

### Quick start

1. Place or mount a model file under the local `models/` directory, or point `MODELS_DIR` elsewhere.
2. Set `MODEL` to the path of the model inside `/models`.
3. Optionally set `LLAMA_CPP_REF` if you want to pin a llama.cpp branch, tag, or commit-ish.
4. Optionally set `ROCM_DOCKER_ARCH` to control which AMD GPU architectures are compiled into the image.
5. Start the service from `docker/services/llama-cpp-rocm`.

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