FROM ubuntu:24.04

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates zsh zstd wget curl procps pciutils \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama via official installer (handles ROCm bundling automatically)
RUN curl -fsSL https://ollama.com/install.sh | OLLAMA_SKIP_START=true sh

EXPOSE 11434

# Set the default shell to loop/wait or drop into zsh
CMD ["/bin/zsh"]
