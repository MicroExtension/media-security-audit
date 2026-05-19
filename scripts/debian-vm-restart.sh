#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-restart.sh --confirm

Restarts the MEDIA Security Audit Docker Compose service without removing
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
  fail "explicit --confirm is required to restart the service"
}

info "stopping service without removing persistent data"
bash scripts/debian-vm-stop.sh --confirm

info "running guarded startup with strict preflight"
bash scripts/debian-vm-start.sh
