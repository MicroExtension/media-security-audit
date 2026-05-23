#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-offline-update-preview-inventory.sh [--verify-manifests]

Lists local offline update preview folders with preview manifest status. This
script is read-only: it does not delete previews, extract archives, apply
updates, build images, restart services, or run scanners.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

OPTION="${1:-}"
VERIFY_MANIFESTS=false

[[ "${OPTION}" != "--help" ]] || {
  usage
  exit 0
}
if [[ "${OPTION}" == "--verify-manifests" ]]; then
  VERIFY_MANIFESTS=true
elif [[ -n "${OPTION}" ]]; then
  fail "unknown option: ${OPTION}"
fi

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"
command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v find >/dev/null 2>&1 || fail "find is required before running this script"
command -v sort >/dev/null 2>&1 || fail "sort is required before running this script"

PREVIEW_DIR="${MEDIA_AUDIT_OFFLINE_UPDATE_PREVIEW_DIR:-reports/offline-update-previews}"

info "offline update preview inventory is read-only; no preview will be removed or applied"
printf 'generated_at_utc=%s\n' "$(date -u +%Y%m%dT%H%M%SZ)"
printf 'offline_update_preview_dir=%s\n' "${PREVIEW_DIR}"
printf 'verify_manifests=%s\n' "${VERIFY_MANIFESTS}"

if [[ ! -d "${PREVIEW_DIR}" ]]; then
  info "offline update preview directory not found: ${PREVIEW_DIR}"
  exit 0
fi

mapfile -t PREVIEWS < <(find "${PREVIEW_DIR}" -mindepth 1 -maxdepth 1 -type d -print | sort)
if [[ "${#PREVIEWS[@]}" -eq 0 ]]; then
  info "no offline update previews found in ${PREVIEW_DIR}"
  exit 0
fi

manifest_value() {
  local manifest="$1"
  local key="$2"
  awk -F= -v key="${key}" '$1 == key {value=substr($0, length(key) + 2)} END {print value}' "${manifest}"
}

ISSUES=0
for PREVIEW in "${PREVIEWS[@]}"; do
  MANIFEST="${PREVIEW}/preview-manifest.txt"
  MANIFEST_STATUS="missing"
  MANIFEST_PATH="none"
  SOURCE_PACKAGE="unknown"
  TOP_LEVEL_SOURCE="unknown"

  if [[ -f "${MANIFEST}" ]]; then
    MANIFEST_PATH="${MANIFEST}"
    SOURCE_PACKAGE="$(manifest_value "${MANIFEST}" source_package)"
    TOP_LEVEL_SOURCE="$(manifest_value "${MANIFEST}" top_level_source)"

    if [[ "${VERIFY_MANIFESTS}" == "true" ]]; then
      if bash scripts/debian-vm-verify-offline-update-preview.sh "${PREVIEW}" >/dev/null; then
        MANIFEST_STATUS="verified"
      else
        MANIFEST_STATUS="failed"
        ISSUES=$((ISSUES + 1))
      fi
    else
      MANIFEST_STATUS="present"
    fi
  elif [[ "${VERIFY_MANIFESTS}" == "true" ]]; then
    ISSUES=$((ISSUES + 1))
  fi

  printf 'offline_update_preview=%s manifest=%s source_package=%s top_level_source=%s preview_path=%s manifest_path=%s\n' \
    "$(basename "${PREVIEW}")" \
    "${MANIFEST_STATUS}" \
    "${SOURCE_PACKAGE:-unknown}" \
    "${TOP_LEVEL_SOURCE:-unknown}" \
    "${PREVIEW}" \
    "${MANIFEST_PATH}"
done

if [[ "${ISSUES}" -gt 0 ]]; then
  fail "offline update preview inventory completed with ${ISSUES} manifest issue(s)"
fi

info "offline update preview inventory complete"
