# local-ai-experiments

Small experiments for running local AI services with Docker.

## ROCm llama.cpp server

The main setup in this repo is a `llama.cpp` server container built for ROCm GPUs. It uses the image `ghcr.io/ggml-org/llama.cpp:server-rocm` and a small shell wrapper to pass through environment variables into the server process.

### Files

- `docker/services/llama-cpp-rocm/docker-compose.yml` - Compose service definition, GPU device passthrough, and default runtime settings.
- `docker/services/llama-cpp-rocm/run-llama-server.sh` - Entrypoint script that converts environment variables into `llama-server` CLI flags.

### Requirements

- Docker with Compose support.
- A ROCm-capable AMD GPU with `/dev/kfd` and `/dev/dri` access.
- A GGUF model file mounted into the container.

### Quick start

1. Place or mount a model file under the local `models/` directory, or point `MODELS_DIR` elsewhere.
2. Set `MODEL` to the path of the model inside `/models`.
3. Start the service from `docker/services/llama-cpp-rocm`.

Example:

```bash
MODEL=/models/Qwen3-Coder-Next-GGUF.gguf docker compose up -d
```

The server listens on port `8080` by default.

### Common configuration

The Compose file already exposes a set of useful environment variables, including:

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