#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-restore-preview.sh <backup.tgz> [preview-dir]

Extracts a MEDIA Security Audit backup archive into a separate preview folder
for inspection. This script does not replace live data folders.
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
PREVIEW_ROOT="${2:-}"

[[ -n "${ARCHIVE}" ]] || {
  usage
  exit 2
}
[[ "${ARCHIVE}" != "--help" ]] || {
  usage
  exit 0
}

command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v tar >/dev/null 2>&1 || fail "tar is required before running this script"

bash scripts/debian-vm-verify-backup.sh "${ARCHIVE}"

if [[ -z "${PREVIEW_ROOT}" ]]; then
  TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  PREVIEW_ROOT="reports/restore-previews/media-audit-restore-preview-${TIMESTAMP}"
fi

for live_folder in data runs reports evidence; do
  [[ "${PREVIEW_ROOT}" != "${live_folder}" ]] \
    || fail "refusing to extract preview over live ${live_folder}/"
done

[[ ! -e "${PREVIEW_ROOT}" ]] || fail "preview destination already exists: ${PREVIEW_ROOT}"

info "creating restore preview folder ${PREVIEW_ROOT}"
mkdir -p "${PREVIEW_ROOT}"

info "extracting backup into preview folder"
tar -xzf "${ARCHIVE}" -C "${PREVIEW_ROOT}"

for folder in data runs reports evidence; do
  [[ -d "${PREVIEW_ROOT}/${folder}" ]] || fail "preview is missing ${folder}/ after extraction"
done

info "restore preview ready: ${PREVIEW_ROOT}"
info "inspect this folder manually before planning any live restore."
