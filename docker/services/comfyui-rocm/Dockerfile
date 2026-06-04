FROM ubuntu:24.04

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates gnupg \
    zsh nano zstd git wget curl usbutils \
    python3-dev python3-pip python3-venv \
    libssl-dev libffi-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install ROCm
RUN wget https://repo.radeon.com/amdgpu-install/7.2.3/ubuntu/noble/amdgpu-install_7.2.3.70203-1_all.deb \
    && apt-get update \
    && apt-get install -y ./amdgpu-install_7.2.3.70203-1_all.deb \
    && rm ./amdgpu-install_7.2.3.70203-1_all.deb \
    && apt-get update && apt-get install -y rocm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone ComfyUI (The standard backend for running high-end image models)
RUN git clone https://github.com/comfyanonymous/ComfyUI.git comfyui

WORKDIR /workspace/comfyui

# Setup Python virtual environment
ENV VIRTUAL_ENV=/opt/comfyui_venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install PyTorch with ROCm support and ComfyUI requirements
# Note: Using rocm6.2 wheel repo as PyTorch nightly/stable typically tracks slightly behind the standalone ROCm releases
RUN pip install --upgrade pip \
    && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2 \
    && pip install -r requirements.txt

EXPOSE 8188

CMD ["python3", "main.py", "--listen", "0.0.0.0"]
