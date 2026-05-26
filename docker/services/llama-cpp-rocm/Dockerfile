FROM ubuntu:24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive

# Install additional packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates gnupg libgomp1 \
    zsh nano zstd git wget curl psutils \
    python3-dev python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install ROCm
RUN wget https://repo.radeon.com/amdgpu-install/7.2.3/ubuntu/noble/amdgpu-install_7.2.3.70203-1_all.deb \
    && apt-get update \
    && apt-get install -y ./amdgpu-install_7.2.3.70203-1_all.deb \
    && rm ./amdgpu-install_7.2.3.70203-1_all.deb \
    && apt-get update && apt-get install -y rocm \
    && rm -rf /var/lib/apt/lists/*


FROM base AS build

# Install build packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 libssl-dev libffi-dev build-essential cmake \
    && rm -rf /var/lib/apt/lists/*
    
ARG LLAMA_CPP_REF=master

WORKDIR /src

RUN git clone --depth 1 --branch "${LLAMA_CPP_REF}" https://github.com/ggml-org/llama.cpp.git .

RUN HIPCXX="$(hipconfig -l)/clang" HIP_PATH="$(hipconfig -R)" \
    cmake -S . -B build \
      -DGGML_HIP=ON \
      -DGGML_HIP_ROCWMMA_FATTN=ON \
      -DAMDGPU_TARGETS="${ROCM_DOCKER_ARCH}" \
      -DGGML_BACKEND_DL=ON \
      -DGGML_CPU_ALL_VARIANTS=ON \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLAMA_BUILD_TESTS=OFF \
    && cmake --build build --config Release -j"$(nproc)" \
    && mkdir -p /app/lib /app/server \
    && find build -name "*.so*" -exec cp -P {} /app/lib \; \
    && cp build/bin/llama-server /app/server/llama-server

FROM base AS runtime

COPY --from=build /app/lib/ /app/
COPY --from=build /app/server/llama-server /app/llama-server

WORKDIR /app

HEALTHCHECK CMD ["curl", "-f", "http://localhost:8080/health"]

ENTRYPOINT ["/app/llama-server"]
