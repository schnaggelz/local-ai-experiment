FROM ubuntu:26.04 AS base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y wget gpg libatomic1 libquadmath0
RUN mkdir --parents --mode=0755 /etc/apt/keyrings

RUN wget https://repo.amd.com/rocm/packages-multi-arch/gpg/rocm.gpg -O - | \
    gpg --dearmor | tee /etc/apt/keyrings/amdrocm.gpg >/dev/null

RUN tee /etc/apt/sources.list.d/rocm.list >/dev/null <<EOF
deb [arch=amd64 signed-by=/etc/apt/keyrings/amdrocm.gpg] https://repo.amd.com/rocm/packages-multi-arch/ubuntu2604 stable main
EOF

RUN apt update

# Set ROCm environment paths
ENV ROCM_PATH=/opt/rocm
ENV PATH=$ROCM_PATH/bin:$PATH
ENV LD_LIBRARY_PATH=$ROCM_PATH/lib:$LD_LIBRARY_PATH

FROM base AS build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 libssl-dev libffi-dev build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

ARG LLAMA_CPP_REF=master

# Default build targets include RDNA3 (gfx1100) and RDNA4 (gfx1201)
ARG ROCM_DOCKER_ARCH="gfx1100;gfx1201"

WORKDIR /src

RUN git clone --depth 1 --branch "${LLAMA_CPP_REF}" https://github.com/ggml-org/llama.cpp.git .

# Build llama.cpp with HIP, FlashAttention, and RPC
RUN CMAKE_PREFIX_PATH=/opt/rocm \
    HIPCXX=/opt/rocm/llvm/bin/clang++ \
    HIP_PATH=/opt/rocm \
    cmake -S . -B build \
      -DCMAKE_C_COMPILER=/opt/rocm/llvm/bin/clang \
      -DCMAKE_CXX_COMPILER=/opt/rocm/llvm/bin/clang++ \
      -DGGML_HIP=ON \
      -DGGML_RPC=ON \
      -DGGML_HIP_ROCWMMA_FATTN=ON \
      -DAMDGPU_TARGETS="${ROCM_DOCKER_ARCH}" \
      -DGGML_BACKEND_DL=ON \
      -DGGML_CPU_ALL_VARIANTS=ON \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLAMA_BUILD_TESTS=OFF \
    && cmake --build build --config Release -j"$(nproc)" \
    && mkdir -p /app/lib /app/bin \
    && find build -name "*.so*" -exec cp -P {} /app/lib \; \
    && cp build/bin/llama-server /app/bin/llama-server \
    && cp build/bin/rpc-server /app/bin/rpc-server

FROM base AS runtime

COPY --from=build /app/lib/ /app/lib/
COPY --from=build /app/bin/ /app/bin/

ENV LD_LIBRARY_PATH=/app/lib:$LD_LIBRARY_PATH
ENV PATH=/app/bin:$PATH

WORKDIR /app

HEALTHCHECK CMD ["curl", "-f", "http://localhost:8080/health"]

# Set the default shell to loop/wait or drop into zsh
CMD ["/bin/zsh"]
