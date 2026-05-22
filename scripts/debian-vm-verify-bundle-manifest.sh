#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-verify-bundle-manifest.sh <bundle.tgz> [manifest.txt]

Checks that a bundle sidecar manifest still matches a local bundle. This script
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

BUNDLE="${1:-}"
MANIFEST="${2:-${BUNDLE}.manifest.txt}"

[[ -n "${BUNDLE}" ]] || {
  usage
  exit 2
}
[[ "${BUNDLE}" != "--help" ]] || {
  usage
  exit 0
}

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"
command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"

[[ -f "${BUNDLE}" ]] || fail "bundle not found: ${BUNDLE}"
[[ -s "${BUNDLE}" ]] || fail "bundle is empty: ${BUNDLE}"
[[ -f "${MANIFEST}" ]] || fail "bundle manifest not found: ${MANIFEST}"
[[ -s "${MANIFEST}" ]] || fail "bundle manifest is empty: ${MANIFEST}"

manifest_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key {value=substr($0, length(key) + 2)} END {print value}' "${MANIFEST}"
}

EXPECTED_BUNDLE="$(manifest_value bundle)"
EXPECTED_SIZE="$(manifest_value size_bytes)"
EXPECTED_SHA256="$(manifest_value sha256)"
EXPECTED_SOURCE_REPORT="$(manifest_value source_report)"
EXPECTED_CONTENTS="$(manifest_value contents)"

case "${EXPECTED_CONTENTS}" in
  handoff_report_only|maintenance_report_only|diagnostics_report_only) ;;
  *) fail "manifest contents value is not recognized" ;;
esac

[[ -n "${EXPECTED_SOURCE_REPORT}" ]] || fail "manifest source_report is missing"
[[ "${EXPECTED_SOURCE_REPORT}" == *.txt ]] || fail "manifest source_report must be a text report"
[[ "${EXPECTED_BUNDLE}" == "$(basename "${BUNDLE}")" ]] || fail "manifest bundle name does not match bundle"
[[ "${EXPECTED_SIZE}" == "$(stat -c '%s' "${BUNDLE}")" ]] || fail "manifest size does not match bundle"
[[ "${EXPECTED_SHA256}" == "$(sha256sum "${BUNDLE}" | awk '{print $1}')" ]] || fail "manifest sha256 does not match bundle"

info "bundle manifest verified: ${MANIFEST}"
