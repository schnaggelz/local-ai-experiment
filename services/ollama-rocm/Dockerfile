FROM ubuntu:26.04

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install additional packages
RUN apt update && apt install -y --no-install-recommends \
    ca-certificates gnupg zsh zstd wget curl \
    libatomic1 libquadmath0

# Download and install GPG key
RUN mkdir --parents --mode=0755 /etc/apt/keyrings
RUN wget https://repo.amd.com/rocm/packages/gpg/rocm.gpg -O - | gpg --dearmor | tee /etc/apt/keyrings/amdrocm.gpg > /dev/null
RUN tee /etc/apt/sources.list.d/rocm.list << EOF
deb [arch=amd64 signed-by=/etc/apt/keyrings/amdrocm.gpg] https://repo.amd.com/rocm/packages-multi-arch/ubuntu2604 stable main
EOF

RUN apt update && apt install -y --no-install-recommends \
     rocminfo amdrocm-core7.13-gfx1100 amdrocm-blas7.13-gfx1100 amdrocm-runtime7.13
#     rocminfo amdrocm-core7.13-gfx1201 amdrocm-blas7.13-gfx1201 amdrocm-runtime7.13

RUN curl -fsSL https://ollama.com/install.sh | sh

RUN rm -rf /var/cache/apt/* && apt clean all

# Set the default shell to loop/wait or drop into zsh
CMD ["/bin/zsh"]
