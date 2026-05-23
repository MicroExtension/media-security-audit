#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-offline-update-preview.sh <package.tgz> [preview-dir]

Verifies and extracts a source-only offline update package into a separate
preview folder for inspection, then writes a preview manifest. This script does
not apply updates, replace the live repository, build images, restart services,
or run scanners.
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
command -v mkdir >/dev/null 2>&1 || fail "mkdir is required before running this script"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"
command -v tar >/dev/null 2>&1 || fail "tar is required before running this script"

bash scripts/debian-vm-verify-offline-update-package.sh "${PACKAGE}"

GENERATED_AT_UTC="$(date -u +%Y%m%dT%H%M%SZ)"

if [[ -z "${PREVIEW_ROOT}" ]]; then
  PACKAGE_NAME="$(basename "${PACKAGE}" .tgz)"
  PREVIEW_ROOT="reports/offline-update-previews/${PACKAGE_NAME}-${GENERATED_AT_UTC}"
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

TOP_LEVEL_SOURCE="$(find "${PREVIEW_ROOT}" -mindepth 1 -maxdepth 1 -type d -print -quit)"

if [[ -z "${TOP_LEVEL_SOURCE}" ]]; then
  fail "offline update preview did not contain a top-level source folder"
fi

PACKAGE_NAME="$(basename "${PACKAGE}")"
PACKAGE_SIZE_BYTES="$(stat -c '%s' "${PACKAGE}")"
PACKAGE_SHA256_LINE="$(sha256sum "${PACKAGE}")"
PACKAGE_SHA256="${PACKAGE_SHA256_LINE%% *}"
TOP_LEVEL_SOURCE_NAME="$(basename "${TOP_LEVEL_SOURCE}")"
PREVIEW_MANIFEST="${PREVIEW_ROOT}/preview-manifest.txt"

info "writing offline update preview manifest ${PREVIEW_MANIFEST}"
cat >"${PREVIEW_MANIFEST}" <<EOF
# MEDIA Security Audit Offline Update Preview Manifest
generated_at_utc=${GENERATED_AT_UTC}
source_package=${PACKAGE_NAME}
source_package_path=${PACKAGE}
source_package_size_bytes=${PACKAGE_SIZE_BYTES}
source_package_sha256=${PACKAGE_SHA256}
preview_root=${PREVIEW_ROOT}
top_level_source=${TOP_LEVEL_SOURCE_NAME}
application=not_implemented
live_replacement=not_performed
scanner_execution=not_performed
EOF

info "offline update preview ready: ${PREVIEW_ROOT}"
info "inspect this folder manually before designing any live offline update application."
