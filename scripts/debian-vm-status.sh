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

info "environment"
if [[ -f ".env" ]]; then
  echo "env_file=present"
  if grep -Eq '^MEDIA_AUDIT_WEB_PASSWORD=.+$' ".env"; then
    echo "web_password=configured"
  else
    echo "web_password=missing"
  fi
else
  echo "env_file=missing"
fi

info "compose configuration"
if docker compose config --quiet >/dev/null 2>&1; then
  echo "compose_config=ready"
else
  echo "compose_config=blocked"
fi

info "compose services"
docker compose ps || true

info "deployment preflight json"
docker compose run --rm media-audit preflight \
  --data-dir /var/lib/media-audit/data \
  --reports-dir /var/lib/media-audit/reports \
  --format json || true
