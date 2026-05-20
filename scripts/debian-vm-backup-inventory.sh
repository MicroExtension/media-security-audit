#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-backup-inventory.sh [--verify-manifests]

Lists local VM backup archives and sidecar manifest status. This script is
read-only: it does not delete backups, extract archives, or restore data.
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

BACKUP_DIR="${MEDIA_AUDIT_BACKUP_DIR:-reports/backups}"

info "backup inventory is read-only; no backup will be removed or restored"
printf 'generated_at_utc=%s\n' "$(date -u +%Y%m%dT%H%M%SZ)"
printf 'backup_dir=%s\n' "${BACKUP_DIR}"
printf 'verify_manifests=%s\n' "${VERIFY_MANIFESTS}"

if [[ ! -d "${BACKUP_DIR}" ]]; then
  info "backup directory not found: ${BACKUP_DIR}"
  exit 0
fi

mapfile -t ARCHIVES < <(find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'media-audit-backup-*.tgz' -print | sort)
if [[ "${#ARCHIVES[@]}" -eq 0 ]]; then
  info "no backup archives found in ${BACKUP_DIR}"
  exit 0
fi

ISSUES=0
for ARCHIVE in "${ARCHIVES[@]}"; do
  MANIFEST="${ARCHIVE}.manifest.txt"
  MANIFEST_STATUS="missing"
  MANIFEST_PATH="none"

  if [[ -f "${MANIFEST}" ]]; then
    MANIFEST_PATH="${MANIFEST}"
    if [[ "${VERIFY_MANIFESTS}" == "true" ]]; then
      if bash scripts/debian-vm-verify-backup-manifest.sh "${ARCHIVE}" >/dev/null; then
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

  printf 'backup=%s size_bytes=%s manifest=%s archive_path=%s manifest_path=%s\n' \
    "$(basename "${ARCHIVE}")" \
    "$(stat -c '%s' "${ARCHIVE}")" \
    "${MANIFEST_STATUS}" \
    "${ARCHIVE}" \
    "${MANIFEST_PATH}"
done

if [[ "${ISSUES}" -gt 0 ]]; then
  fail "backup inventory completed with ${ISSUES} manifest issue(s)"
fi

info "backup inventory complete"
