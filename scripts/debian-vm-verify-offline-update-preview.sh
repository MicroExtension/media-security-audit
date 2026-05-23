#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-verify-offline-update-preview.sh <preview-dir> [--package <package.tgz>]

Checks that an offline update preview manifest still matches the source package
and extracted source folder. This script does not extract, apply, build,
restart, or run scanners.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

PREVIEW_ROOT="${1:-}"
PACKAGE_OVERRIDE=""

[[ -n "${PREVIEW_ROOT}" ]] || {
  usage
  exit 2
}
[[ "${PREVIEW_ROOT}" != "--help" ]] || {
  usage
  exit 0
}

shift || true

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --package)
      [[ "$#" -ge 2 ]] || fail "--package requires a path"
      PACKAGE_OVERRIDE="$2"
      shift 2
      ;;
    --package=*)
      PACKAGE_OVERRIDE="${1#--package=}"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"
command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v pwd >/dev/null 2>&1 || fail "pwd is required before running this script"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"

[[ -d "${PREVIEW_ROOT}" ]] || fail "offline update preview folder not found: ${PREVIEW_ROOT}"

PREVIEW_MANIFEST="${PREVIEW_ROOT}/preview-manifest.txt"
[[ -f "${PREVIEW_MANIFEST}" ]] || fail "offline update preview manifest not found: ${PREVIEW_MANIFEST}"
[[ -s "${PREVIEW_MANIFEST}" ]] || fail "offline update preview manifest is empty: ${PREVIEW_MANIFEST}"

manifest_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key {value=substr($0, length(key) + 2)} END {print value}' "${PREVIEW_MANIFEST}"
}

canonical_dir() {
  local path="$1"
  (cd "${path}" && pwd -P)
}

EXPECTED_SOURCE_PACKAGE="$(manifest_value source_package)"
EXPECTED_SOURCE_PACKAGE_PATH="$(manifest_value source_package_path)"
EXPECTED_SOURCE_PACKAGE_SIZE="$(manifest_value source_package_size_bytes)"
EXPECTED_SOURCE_PACKAGE_SHA256="$(manifest_value source_package_sha256)"
EXPECTED_PREVIEW_ROOT="$(manifest_value preview_root)"
EXPECTED_TOP_LEVEL_SOURCE="$(manifest_value top_level_source)"
EXPECTED_APPLICATION="$(manifest_value application)"
EXPECTED_LIVE_REPLACEMENT="$(manifest_value live_replacement)"
EXPECTED_SCANNER_EXECUTION="$(manifest_value scanner_execution)"

[[ -n "${EXPECTED_SOURCE_PACKAGE}" ]] || fail "preview manifest source_package is missing"
[[ -n "${EXPECTED_SOURCE_PACKAGE_PATH}" ]] || fail "preview manifest source_package_path is missing"
[[ -n "${EXPECTED_SOURCE_PACKAGE_SIZE}" ]] || fail "preview manifest source_package_size_bytes is missing"
[[ -n "${EXPECTED_SOURCE_PACKAGE_SHA256}" ]] || fail "preview manifest source_package_sha256 is missing"
[[ -n "${EXPECTED_PREVIEW_ROOT}" ]] || fail "preview manifest preview_root is missing"
[[ -n "${EXPECTED_TOP_LEVEL_SOURCE}" ]] || fail "preview manifest top_level_source is missing"

if [[ -d "${EXPECTED_PREVIEW_ROOT}" ]]; then
  [[ "$(canonical_dir "${EXPECTED_PREVIEW_ROOT}")" == "$(canonical_dir "${PREVIEW_ROOT}")" ]] \
    || fail "preview manifest preview_root does not match provided folder"
else
  [[ "${EXPECTED_PREVIEW_ROOT}" == "${PREVIEW_ROOT}" ]] \
    || fail "preview manifest preview_root does not match provided folder"
fi

[[ -d "${PREVIEW_ROOT}/${EXPECTED_TOP_LEVEL_SOURCE}" ]] \
  || fail "preview top-level source folder not found: ${EXPECTED_TOP_LEVEL_SOURCE}"

[[ "${EXPECTED_APPLICATION}" == "not_implemented" ]] \
  || fail "preview manifest application status is not recognized"
[[ "${EXPECTED_LIVE_REPLACEMENT}" == "not_performed" ]] \
  || fail "preview manifest live replacement status is not recognized"
[[ "${EXPECTED_SCANNER_EXECUTION}" == "not_performed" ]] \
  || fail "preview manifest scanner execution status is not recognized"

PACKAGE="${PACKAGE_OVERRIDE:-${EXPECTED_SOURCE_PACKAGE_PATH}}"
[[ -f "${PACKAGE}" ]] \
  || fail "source package not found; pass --package if it was copied elsewhere"
[[ -s "${PACKAGE}" ]] || fail "source package is empty: ${PACKAGE}"
[[ "$(basename "${PACKAGE}")" == "${EXPECTED_SOURCE_PACKAGE}" ]] \
  || fail "preview manifest source package name does not match package"
[[ "$(stat -c '%s' "${PACKAGE}")" == "${EXPECTED_SOURCE_PACKAGE_SIZE}" ]] \
  || fail "preview manifest source package size does not match package"

PACKAGE_SHA256_LINE="$(sha256sum "${PACKAGE}")"
PACKAGE_SHA256="${PACKAGE_SHA256_LINE%% *}"
[[ "${PACKAGE_SHA256}" == "${EXPECTED_SOURCE_PACKAGE_SHA256}" ]] \
  || fail "preview manifest source package SHA-256 does not match package"

info "offline update preview manifest verified: ${PREVIEW_MANIFEST}"
