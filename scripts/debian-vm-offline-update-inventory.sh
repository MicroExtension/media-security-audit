#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-offline-update-inventory.sh [--verify-manifests]

Lists local offline update packages with sidecar manifest status. This script
is read-only: it does not delete packages, extract archives, apply updates,
build images, restart services, or run scanners.
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

command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v find >/dev/null 2>&1 || fail "find is required before running this script"
command -v sort >/dev/null 2>&1 || fail "sort is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"

PACKAGE_DIR="${MEDIA_AUDIT_OFFLINE_UPDATE_DIR:-dist/offline-updates}"

info "offline update package inventory is read-only; no package will be removed or applied"
printf 'generated_at_utc=%s\n' "$(date -u +%Y%m%dT%H%M%SZ)"
printf 'offline_update_dir=%s\n' "${PACKAGE_DIR}"
printf 'verify_manifests=%s\n' "${VERIFY_MANIFESTS}"

if [[ ! -d "${PACKAGE_DIR}" ]]; then
  info "offline update package directory not found: ${PACKAGE_DIR}"
  exit 0
fi

mapfile -t PACKAGES < <(find "${PACKAGE_DIR}" -maxdepth 1 -type f -name 'media-audit-offline-update-*.tgz' -print | sort)
if [[ "${#PACKAGES[@]}" -eq 0 ]]; then
  info "no offline update packages found in ${PACKAGE_DIR}"
  exit 0
fi

ISSUES=0
for PACKAGE in "${PACKAGES[@]}"; do
  MANIFEST="${PACKAGE}.manifest.txt"
  MANIFEST_STATUS="missing"
  MANIFEST_PATH="none"

  if [[ -f "${MANIFEST}" ]]; then
    MANIFEST_PATH="${MANIFEST}"
    if [[ "${VERIFY_MANIFESTS}" == "true" ]]; then
      if bash scripts/debian-vm-verify-offline-update-package.sh "${PACKAGE}" >/dev/null; then
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

  printf 'offline_update_package=%s size_bytes=%s manifest=%s package_path=%s manifest_path=%s\n' \
    "$(basename "${PACKAGE}")" \
    "$(stat -c '%s' "${PACKAGE}")" \
    "${MANIFEST_STATUS}" \
    "${PACKAGE}" \
    "${MANIFEST_PATH}"
done

if [[ "${ISSUES}" -gt 0 ]]; then
  fail "offline update package inventory completed with ${ISSUES} manifest issue(s)"
fi

info "offline update package inventory complete"
