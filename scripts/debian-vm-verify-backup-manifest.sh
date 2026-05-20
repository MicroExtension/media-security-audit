#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-verify-backup-manifest.sh <backup.tgz> [manifest.txt]

Checks that a backup sidecar manifest still matches a local archive. This script
does not extract or restore data.
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
MANIFEST="${2:-${ARCHIVE}.manifest.txt}"

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
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"

[[ -f "${ARCHIVE}" ]] || fail "backup archive not found: ${ARCHIVE}"
[[ -s "${ARCHIVE}" ]] || fail "backup archive is empty: ${ARCHIVE}"
[[ -f "${MANIFEST}" ]] || fail "backup manifest not found: ${MANIFEST}"
[[ -s "${MANIFEST}" ]] || fail "backup manifest is empty: ${MANIFEST}"

manifest_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key {value=substr($0, length(key) + 2)} END {print value}' "${MANIFEST}"
}

EXPECTED_ARCHIVE="$(manifest_value archive)"
EXPECTED_SIZE="$(manifest_value size_bytes)"
EXPECTED_SHA256="$(manifest_value sha256)"
EXPECTED_VERIFICATION="$(manifest_value verification)"

[[ "${EXPECTED_ARCHIVE}" == "$(basename "${ARCHIVE}")" ]] || fail "manifest archive name does not match backup"
[[ "${EXPECTED_SIZE}" == "$(stat -c '%s' "${ARCHIVE}")" ]] || fail "manifest size does not match backup"
[[ "${EXPECTED_SHA256}" == "$(sha256sum "${ARCHIVE}" | awk '{print $1}')" ]] || fail "manifest sha256 does not match backup"
[[ "verification=${EXPECTED_VERIFICATION}" == "verification=passed" ]] || fail "manifest verification status is not passed"

info "backup manifest verified: ${MANIFEST}"
