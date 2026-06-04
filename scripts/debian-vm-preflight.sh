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

STRICT=false
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=true
  shift
fi
[[ $# -eq 0 ]] || fail "usage: bash scripts/debian-vm-preflight.sh [--strict]"

[[ -f ".env" ]] || fail "copy .env.example to .env and set MEDIA_AUDIT_WEB_PASSWORD first"
grep -Eq '^MEDIA_AUDIT_WEB_PASSWORD=.+$' ".env" \
  || fail "set MEDIA_AUDIT_WEB_PASSWORD in .env before running this script"

info "creating persistent local folders"
mkdir -p data runs reports evidence

for folder in data runs reports evidence; do
  [[ -d "${folder}" ]] || fail "${folder} was not created"
  [[ -w "${folder}" ]] || fail "${folder} is not writable by the current user"
done

info "validating Docker Compose configuration"
docker compose config --quiet

info "building local media-audit image"
docker compose build media-audit

preflight_flags=()
if [[ "${STRICT}" == "true" ]]; then
  preflight_flags+=(--strict)
  info "running strict deployment preflight"
else
  info "running deployment preflight"
fi

docker compose run --rm media-audit media-audit preflight \
  --data-dir /var/lib/media-audit/data \
  --reports-dir /var/lib/media-audit/reports \
  "${preflight_flags[@]}"

info "preflight completed; run 'docker compose up -d' when ready to start the service"
