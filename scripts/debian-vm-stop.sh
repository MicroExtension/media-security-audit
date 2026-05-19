#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-stop.sh --confirm

Stops the MEDIA Security Audit Docker Compose service without removing
containers, images, volumes, or persistent folders.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

CONFIRM="${1:-}"
[[ "${CONFIRM}" == "--help" ]] && {
  usage
  exit 0
}
[[ "${CONFIRM}" == "--confirm" ]] || {
  usage
  fail "explicit --confirm is required to stop the service"
}

command -v docker >/dev/null 2>&1 || fail "docker is required before running this script"
docker compose version >/dev/null 2>&1 || fail "docker compose v2 is required before running this script"

info "stopping media-audit service without removing persistent data"
docker compose stop media-audit

info "service status"
docker compose ps
