#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
state_dir=${SDKM_STATE_DIR:-"$script_dir/.sdkm"}
downloads_dir=${SDKM_DOWNLOADS_DIR:-"$state_dir/downloads"}
target_image_dir=${SDKM_TARGET_IMAGE_DIR:-"$state_dir/nvidia_sdk"}
image_name=${SDKMANAGER_IMAGE:-sdkmanager:latest}
login_type=${SDKM_LOGIN_TYPE:-devzone}
docker_network=${SDKM_DOCKER_NETWORK:-host}
media_dir=${SDKM_MEDIA_DIR:-"/media/$USER"}
compose_file=${SDKM_COMPOSE_FILE:-"$script_dir/docker-compose.yml"}

usage() {
  cat <<'EOF'
Usage:
  sdkmanager-docker.sh

Environment:
  SDKMANAGER_IMAGE       Docker image name. Default: sdkmanager:latest
  SDKM_DOCKER_NETWORK    Docker network mode. Default: host
  SDKM_MEDIA_DIR         Host media path passed into the container. Default: /media/$USER
  SDKM_STATE_DIR         Host directory for persistent SDK Manager state
  SDKM_DOWNLOADS_DIR     Host directory for downloads
  SDKM_TARGET_IMAGE_DIR  Host directory for generated flash images
  SDKM_COMPOSE_FILE      Override the compose file path

Examples:
  ./sdkmanager-docker.sh
EOF
}

if [[ $# -gt 0 ]]; then
  usage >&2
  exit 1
fi

mkdir -p "$downloads_dir" "$target_image_dir"

export SDKMANAGER_IMAGE="$image_name"
export SDKM_DOCKER_NETWORK="$docker_network"
export SDKM_MEDIA_DIR="$media_dir"
export SDKM_DOWNLOADS_DIR="$downloads_dir"
export SDKM_TARGET_IMAGE_DIR="$target_image_dir"

exec docker compose -f "$compose_file" run --rm sdkmanager