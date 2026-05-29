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
  sdkmanager-docker.sh query [extra sdkmanager args]
  sdkmanager-docker.sh list-connected [extra sdkmanager args]
  sdkmanager-docker.sh download-only [extra sdkmanager args]
  sdkmanager-docker.sh flash [extra sdkmanager args]

Environment:
  SDKMANAGER_IMAGE       Docker image name. Default: sdkmanager:latest
  SDKM_LOGIN_TYPE        SDK Manager login type. Default: devzone
  SDKM_DOCKER_NETWORK    Docker network mode. Default: host
  SDKM_MEDIA_DIR         Host media path passed into the container. Default: /media/$USER
  SDKM_STATE_DIR         Host directory for persistent SDK Manager state
  SDKM_DOWNLOADS_DIR     Host directory for downloads
  SDKM_TARGET_IMAGE_DIR  Host directory for generated flash images
  SDKM_COMPOSE_FILE      Override the compose file path
  JETPACK_VERSION        Required for flash. Example: 5.1.4
  JETSON_TARGET          Required for flash. Example: JETSON_AGX_XAVIER_TARGETS
  SDKM_USB_PORT          Optional USB port selector, from --list-connected
  SDKM_ARCHIVED_VERSIONS Set to 1 to add --archived-versions
  SDKM_AUTO              Set to 1 to add --auto
  SDKM_STAY_LOGGED_IN    true/false. Default: true
  SDKM_COLLECT_USAGE     enable/disable. Default: disable

Examples:
  ./sdkmanager-docker.sh query --product Jetson --show-all-versions
  ./sdkmanager-docker.sh list-connected --product Jetson
  JETPACK_VERSION=5.1.4 JETSON_TARGET=JETSON_AGX_XAVIER_TARGETS ./sdkmanager-docker.sh download-only
  JETPACK_VERSION=5.1.4 JETSON_TARGET=JETSON_AGX_XAVIER_TARGETS ./sdkmanager-docker.sh flash
EOF
}

require_env() {
  local var_name=$1
  if [[ -z "${!var_name:-}" ]]; then
    printf 'Missing required environment variable: %s\n' "$var_name" >&2
    exit 1
  fi
}

shell_join() {
  local joined=""
  local arg

  for arg in "$@"; do
    joined+=" $(printf '%q' "$arg")"
  done

  printf '%s' "${joined# }"
}

command_name=${1:-}
if [[ -z "$command_name" ]]; then
  usage
  exit 1
fi
shift || true

mkdir -p "$downloads_dir" "$target_image_dir"

export SDKMANAGER_IMAGE="$image_name"
export SDKM_DOCKER_NETWORK="$docker_network"
export SDKM_MEDIA_DIR="$media_dir"
export SDKM_DOWNLOADS_DIR="$downloads_dir"
export SDKM_TARGET_IMAGE_DIR="$target_image_dir"
export SDKM_LOGIN_TYPE="$login_type"
export SDKM_EXTRA_ARGS="$(shell_join "$@")"

service_name=

case "$command_name" in
  query)
    service_name=sdkmanager-query
    ;;
  list-connected)
    service_name=sdkmanager-list-connected
    ;;
  download-only)
    require_env JETPACK_VERSION
    require_env JETSON_TARGET
    service_name=sdkmanager-download-only
    ;;
  flash)
    require_env JETPACK_VERSION
    require_env JETSON_TARGET
    service_name=sdkmanager-flash
    ;;
  -h|--help|help)
    usage
    exit 0
    ;;
  *)
    printf 'Unknown command: %s\n\n' "$command_name" >&2
    usage >&2
    exit 1
    ;;
esac

  exec docker compose -f "$compose_file" run --rm "$service_name"