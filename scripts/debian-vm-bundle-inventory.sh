#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-bundle-inventory.sh [--verify-manifests]

Lists local handoff, maintenance, and support bundles with sidecar manifest
status. This script is read-only: it does not delete bundles, extract archives,
or restore data.
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

HANDOFF_DIR="${MEDIA_AUDIT_HANDOFF_BUNDLE_DIR:-${MEDIA_AUDIT_HANDOFF_DIR:-reports/handoff}}"
MAINTENANCE_DIR="${MEDIA_AUDIT_MAINTENANCE_BUNDLE_DIR:-${MEDIA_AUDIT_MAINTENANCE_DIR:-reports/maintenance}}"
SUPPORT_DIR="${MEDIA_AUDIT_SUPPORT_BUNDLE_DIR:-${MEDIA_AUDIT_SUPPORT_DIR:-reports/support}}"

info "bundle inventory is read-only; no bundle will be removed or restored"
printf 'generated_at_utc=%s\n' "$(date -u +%Y%m%dT%H%M%SZ)"
printf 'verify_manifests=%s\n' "${VERIFY_MANIFESTS}"

ISSUES=0
FOUND=0

inventory_family() {
  local family="$1"
  local bundle_dir="$2"
  local pattern="$3"

  printf 'bundle_family=%s bundle_dir=%s\n' "${family}" "${bundle_dir}"
  if [[ ! -d "${bundle_dir}" ]]; then
    info "bundle directory not found for ${family}: ${bundle_dir}"
    return
  fi

  local bundles=()
  mapfile -t bundles < <(find "${bundle_dir}" -maxdepth 1 -type f -name "${pattern}" -print | sort)
  if [[ "${#bundles[@]}" -eq 0 ]]; then
    info "no ${family} bundles found in ${bundle_dir}"
    return
  fi

  local bundle
  for bundle in "${bundles[@]}"; do
    FOUND=$((FOUND + 1))
    local manifest="${bundle}.manifest.txt"
    local manifest_status="missing"
    local manifest_path="none"

    if [[ -f "${manifest}" ]]; then
      manifest_path="${manifest}"
      if [[ "${VERIFY_MANIFESTS}" == "true" ]]; then
        if bash scripts/debian-vm-verify-bundle-manifest.sh "${bundle}" >/dev/null; then
          manifest_status="verified"
        else
          manifest_status="failed"
          ISSUES=$((ISSUES + 1))
        fi
      else
        manifest_status="present"
      fi
    elif [[ "${VERIFY_MANIFESTS}" == "true" ]]; then
      ISSUES=$((ISSUES + 1))
    fi

    printf 'bundle_family=%s bundle=%s size_bytes=%s manifest=%s bundle_path=%s manifest_path=%s\n' \
      "${family}" \
      "$(basename "${bundle}")" \
      "$(stat -c '%s' "${bundle}")" \
      "${manifest_status}" \
      "${bundle}" \
      "${manifest_path}"
  done
}

inventory_family "handoff" "${HANDOFF_DIR}" "media-audit-handoff-*.tgz"
inventory_family "maintenance" "${MAINTENANCE_DIR}" "media-audit-maintenance-*.tgz"
inventory_family "support" "${SUPPORT_DIR}" "media-audit-support-*.tgz"

if [[ "${FOUND}" -eq 0 ]]; then
  info "no bundles found"
fi

if [[ "${ISSUES}" -gt 0 ]]; then
  fail "bundle inventory completed with ${ISSUES} manifest issue(s)"
fi

info "bundle inventory complete"
