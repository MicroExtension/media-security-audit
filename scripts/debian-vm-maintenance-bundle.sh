#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v find >/dev/null 2>&1 || fail "find is required before running this script"
command -v sort >/dev/null 2>&1 || fail "sort is required before running this script"
command -v tail >/dev/null 2>&1 || fail "tail is required before running this script"
command -v tar >/dev/null 2>&1 || fail "tar is required before running this script"

MAINTENANCE_DIR="${MEDIA_AUDIT_MAINTENANCE_DIR:-reports/maintenance}"
BUNDLE_DIR="${MEDIA_AUDIT_MAINTENANCE_BUNDLE_DIR:-${MAINTENANCE_DIR}}"
mkdir -p "${MAINTENANCE_DIR}" "${BUNDLE_DIR}"
[[ -w "${MAINTENANCE_DIR}" ]] || fail "${MAINTENANCE_DIR} is not writable by the current user"
[[ -w "${BUNDLE_DIR}" ]] || fail "${BUNDLE_DIR} is not writable by the current user"

info "generating fresh maintenance report"
MAINTENANCE_STATUS=0
MEDIA_AUDIT_MAINTENANCE_DIR="${MAINTENANCE_DIR}" bash scripts/debian-vm-maintenance-report.sh || MAINTENANCE_STATUS=$?

LATEST_REPORT="$(
  find "${MAINTENANCE_DIR}" -maxdepth 1 -type f -name 'media-audit-maintenance-*.txt' -print \
    | sort \
    | tail -n 1
)"
[[ -n "${LATEST_REPORT}" ]] || fail "no maintenance report was generated"
REPORT_NAME="$(basename "${LATEST_REPORT}")"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BUNDLE="${BUNDLE_DIR}/media-audit-maintenance-${TIMESTAMP}.tgz"

info "writing maintenance bundle ${BUNDLE}"
tar -czf "${BUNDLE}" -C "${MAINTENANCE_DIR}" "${REPORT_NAME}"

info "maintenance bundle ready: ${BUNDLE}"
info "review before sharing; bundle contains the maintenance report only, not customer folders or application logs."
exit "${MAINTENANCE_STATUS}"
