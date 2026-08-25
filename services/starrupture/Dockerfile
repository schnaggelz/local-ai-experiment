FROM ubuntu:24.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN dpkg --add-architecture i386 && \
    apt update && \
    apt install -y --no-install-recommends \
        ca-certificates \
        lib32gcc-s1 \
        lib32stdc++6 \
        zsh \
        curl \
        wget \
        tar \
        locales && \
    locale-gen en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Create a non-root steam user
RUN useradd -m -s /bin/bash steam
USER steam
WORKDIR /home/steam

# Download and extract SteamCMD
RUN mkdir -p /home/steam/steamcmd /home/steam/starrupture && \
    curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf - -C /home/steam/steamcmd

COPY ./scripts /home/steam/server/

# Set the default shell to loop/wait or drop into zsh
CMD ["/bin/zsh"]
