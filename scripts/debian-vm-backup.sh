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

command -v tar >/dev/null 2>&1 || fail "tar is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"

for folder in data runs reports evidence; do
  [[ -d "${folder}" ]] || fail "${folder} is missing; run the VM preflight helper first"
done

BACKUP_DIR="${MEDIA_AUDIT_BACKUP_DIR:-reports/backups}"
mkdir -p "${BACKUP_DIR}"
[[ -w "${BACKUP_DIR}" ]] || fail "${BACKUP_DIR} is not writable by the current user"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="${BACKUP_DIR}/media-audit-backup-${TIMESTAMP}.tgz"

info "creating workspace backup ${ARCHIVE}"
tar \
  --exclude='./reports/backups' \
  --exclude='reports/backups' \
  -czf "${ARCHIVE}" \
  data runs reports evidence

[[ -s "${ARCHIVE}" ]] || fail "backup archive was not created"

info "backup complete: ${ARCHIVE}"
