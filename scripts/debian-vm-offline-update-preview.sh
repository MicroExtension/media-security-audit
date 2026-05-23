#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-offline-update-preview.sh <package.tgz> [preview-dir]

Verifies and extracts a source-only offline update package into a separate
preview folder for inspection. This script does not apply updates, replace the
live repository, build images, restart services, or run scanners.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

PACKAGE="${1:-}"
PREVIEW_ROOT="${2:-}"

[[ -n "${PACKAGE}" ]] || {
  usage
  exit 2
}
[[ "${PACKAGE}" != "--help" ]] || {
  usage
  exit 0
}

command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v find >/dev/null 2>&1 || fail "find is required before running this script"
command -v tar >/dev/null 2>&1 || fail "tar is required before running this script"

bash scripts/debian-vm-verify-offline-update-package.sh "${PACKAGE}"

if [[ -z "${PREVIEW_ROOT}" ]]; then
  TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  PACKAGE_NAME="$(basename "${PACKAGE}" .tgz)"
  PREVIEW_ROOT="reports/offline-update-previews/${PACKAGE_NAME}-${TIMESTAMP}"
fi

for live_folder in .git data runs reports evidence; do
  [[ "${PREVIEW_ROOT}" != "${live_folder}" ]] \
    || fail "refusing to extract offline update preview over live ${live_folder}/"
done

[[ ! -e "${PREVIEW_ROOT}" ]] || fail "preview destination already exists: ${PREVIEW_ROOT}"

info "creating offline update preview folder ${PREVIEW_ROOT}"
mkdir -p "${PREVIEW_ROOT}"

info "extracting offline update package into preview folder"
tar -xzf "${PACKAGE}" -C "${PREVIEW_ROOT}"

if [[ -z "$(find "${PREVIEW_ROOT}" -mindepth 1 -maxdepth 1 -type d -print -quit)" ]]; then
  fail "offline update preview did not contain a top-level source folder"
fi

info "offline update preview ready: ${PREVIEW_ROOT}"
info "inspect this folder manually before designing any live offline update application."
