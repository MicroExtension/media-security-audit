#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

command -v docker >/dev/null 2>&1 || fail "docker is required before running this script"
docker compose version >/dev/null 2>&1 || fail "docker compose v2 is required before running this script"

[[ -f ".env" ]] || fail "run scripts/debian-vm-init-env.sh before starting the service"
grep -Eq '^MEDIA_AUDIT_WEB_PASSWORD=.+$' ".env" \
  || fail "set MEDIA_AUDIT_WEB_PASSWORD in .env before starting the service"

info "running deployment preflight before startup"
bash scripts/debian-vm-preflight.sh

info "starting media-audit service"
docker compose up -d

info "service status"
docker compose ps
