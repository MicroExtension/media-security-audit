#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-backup-manifest.sh <backup.tgz>

Verifies a backup archive, then writes a sidecar manifest containing size and
SHA-256 metadata. This script does not extract or restore data.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

ARCHIVE="${1:-}"

[[ -n "${ARCHIVE}" ]] || {
  usage
  exit 2
}
[[ "${ARCHIVE}" != "--help" ]] || {
  usage
  exit 0
}

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"
command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"

[[ -f "${ARCHIVE}" ]] || fail "backup archive not found: ${ARCHIVE}"
[[ -s "${ARCHIVE}" ]] || fail "backup archive is empty: ${ARCHIVE}"

info "verifying backup before manifest generation"
bash scripts/debian-vm-verify-backup.sh "${ARCHIVE}"

ARCHIVE_NAME="$(basename "${ARCHIVE}")"
SHA256="$(sha256sum "${ARCHIVE}" | awk '{print $1}')"
SIZE_BYTES="$(stat -c '%s' "${ARCHIVE}")"
GENERATED_AT="$(date -u +%Y%m%dT%H%M%SZ)"
MANIFEST="${ARCHIVE}.manifest.txt"

info "writing backup manifest ${MANIFEST}"
cat >"${MANIFEST}" <<EOF
# MEDIA Security Audit VM Backup Manifest
generated_at_utc=${GENERATED_AT}
archive=${ARCHIVE_NAME}
size_bytes=${SIZE_BYTES}
sha256=${SHA256}
verification=passed
EOF

info "backup manifest ready: ${MANIFEST}"
info "review the manifest with the backup before copying it outside the customer site."
