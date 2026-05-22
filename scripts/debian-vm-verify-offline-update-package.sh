#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-verify-offline-update-package.sh <package.tgz> [manifest.txt]

Checks that an offline update package sidecar manifest still matches a local
package. This script does not extract, apply, build, restart, or run scanners.
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
MANIFEST="${2:-${PACKAGE}.manifest.txt}"

[[ -n "${PACKAGE}" ]] || {
  usage
  exit 2
}
[[ "${PACKAGE}" != "--help" ]] || {
  usage
  exit 0
}

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"
command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"

[[ -f "${PACKAGE}" ]] || fail "offline update package not found: ${PACKAGE}"
[[ -s "${PACKAGE}" ]] || fail "offline update package is empty: ${PACKAGE}"
[[ -f "${MANIFEST}" ]] || fail "offline update package manifest not found: ${MANIFEST}"
[[ -s "${MANIFEST}" ]] || fail "offline update package manifest is empty: ${MANIFEST}"

manifest_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key {value=substr($0, length(key) + 2)} END {print value}' "${MANIFEST}"
}

EXPECTED_PACKAGE="$(manifest_value package)"
EXPECTED_SOURCE_BRANCH="$(manifest_value source_branch)"
EXPECTED_SOURCE_COMMIT="$(manifest_value source_commit)"
EXPECTED_SIZE="$(manifest_value size_bytes)"
EXPECTED_SHA256="$(manifest_value sha256)"
EXPECTED_CONTENTS="$(manifest_value contents)"
EXPECTED_EXCLUDES="$(manifest_value excludes)"
EXPECTED_APPLICATION="$(manifest_value application)"

[[ "${EXPECTED_PACKAGE}" == "$(basename "${PACKAGE}")" ]] || fail "manifest package name does not match package"
[[ -n "${EXPECTED_SOURCE_BRANCH}" ]] || fail "manifest source_branch is missing"
[[ -n "${EXPECTED_SOURCE_COMMIT}" ]] || fail "manifest source_commit is missing"
[[ "${EXPECTED_SIZE}" == "$(stat -c '%s' "${PACKAGE}")" ]] || fail "manifest size does not match package"
[[ "${EXPECTED_SHA256}" == "$(sha256sum "${PACKAGE}" | awk '{print $1}')" ]] || fail "manifest sha256 does not match package"
[[ "${EXPECTED_CONTENTS}" == "git_tracked_source_only" ]] || fail "manifest contents value is not recognized"
[[ "${EXPECTED_EXCLUDES}" == "data,runs,reports,evidence,.env,.git" ]] || fail "manifest excludes value is not recognized"
[[ "${EXPECTED_APPLICATION}" == "not_implemented" ]] || fail "manifest application status is not recognized"

info "offline update package manifest verified: ${MANIFEST}"
