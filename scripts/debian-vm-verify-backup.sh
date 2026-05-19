#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-verify-backup.sh <backup.tgz> [--verbose]

Checks that a MEDIA Security Audit backup archive can be listed and contains
the expected persistent folders. This script does not extract or restore data.
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
VERBOSE="${2:-}"

[[ -n "${ARCHIVE}" ]] || {
  usage
  exit 2
}
[[ "${ARCHIVE}" != "--help" ]] || {
  usage
  exit 0
}
[[ "${VERBOSE}" == "" || "${VERBOSE}" == "--verbose" ]] || fail "unknown option: ${VERBOSE}"

command -v tar >/dev/null 2>&1 || fail "tar is required before running this script"
[[ -f "${ARCHIVE}" ]] || fail "backup archive not found: ${ARCHIVE}"
[[ -s "${ARCHIVE}" ]] || fail "backup archive is empty: ${ARCHIVE}"

LISTING="$(tar -tzf "${ARCHIVE}")"

for folder in data runs reports evidence; do
  if ! grep -Eq "^${folder}(/|$)" <<<"${LISTING}"; then
    fail "backup archive is missing ${folder}/"
  fi
done

if [[ "${VERBOSE}" == "--verbose" ]]; then
  printf '%s\n' "${LISTING}"
fi

info "backup archive verified: ${ARCHIVE}"
