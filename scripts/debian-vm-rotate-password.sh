#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-rotate-password.sh --confirm

Rotates MEDIA_AUDIT_WEB_PASSWORD in .env, keeps authentication enabled, and
creates a local .env timestamped backup before writing the new value.
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
  fail "explicit --confirm is required to rotate the web password"
}

command -v cp >/dev/null 2>&1 || fail "cp is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v python3 >/dev/null 2>&1 || fail "python3 is required to generate a strong password"

[[ -f ".env" ]] || fail ".env is required before rotating the web password"
[[ -w ".env" ]] || fail ".env is not writable by the current user"

PASSWORD="$(
  python3 - <<'PY'
import secrets

print(secrets.token_urlsafe(24))
PY
)"
[[ -n "${PASSWORD}" ]] || fail "password generation failed"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP=".env.${TIMESTAMP}.bak"
cp -p ".env" "${BACKUP}"
chmod 600 "${BACKUP}"

python3 - "${PASSWORD}" <<'PY'
from pathlib import Path
import sys

password = sys.argv[1]
path = Path(".env")
lines = path.read_text(encoding="utf-8").splitlines()


def upsert(key: str, value: str) -> None:
    prefix = f"{key}="
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = f"{key}={value}"
            return
    lines.append(f"{key}={value}")


upsert("MEDIA_AUDIT_REQUIRE_AUTH", "true")
upsert("MEDIA_AUDIT_WEB_PASSWORD", password)
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
chmod 600 ".env"

info ".env web password rotated; backup created at ${BACKUP}"
info "store updated MEDIA_AUDIT_WEB_PASSWORD from .env in the maintenance password vault"
info "run scripts/debian-vm-restart.sh --confirm during an approved maintenance window to apply the change"
