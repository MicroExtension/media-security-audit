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

HANDOFF_DIR="${MEDIA_AUDIT_HANDOFF_DIR:-reports/handoff}"
BUNDLE_DIR="${MEDIA_AUDIT_HANDOFF_BUNDLE_DIR:-${HANDOFF_DIR}}"
mkdir -p "${HANDOFF_DIR}" "${BUNDLE_DIR}"
[[ -w "${HANDOFF_DIR}" ]] || fail "${HANDOFF_DIR} is not writable by the current user"
[[ -w "${BUNDLE_DIR}" ]] || fail "${BUNDLE_DIR} is not writable by the current user"

info "generating fresh handoff report"
HANDOFF_STATUS=0
MEDIA_AUDIT_HANDOFF_DIR="${HANDOFF_DIR}" bash scripts/debian-vm-handoff-report.sh || HANDOFF_STATUS=$?

LATEST_REPORT="$(
  find "${HANDOFF_DIR}" -maxdepth 1 -type f -name 'media-audit-handoff-*.txt' -print \
    | sort \
    | tail -n 1
)"
[[ -n "${LATEST_REPORT}" ]] || fail "no handoff report was generated"
REPORT_NAME="$(basename "${LATEST_REPORT}")"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BUNDLE="${BUNDLE_DIR}/media-audit-handoff-${TIMESTAMP}.tgz"

info "writing handoff bundle ${BUNDLE}"
tar -czf "${BUNDLE}" -C "${HANDOFF_DIR}" "${REPORT_NAME}"

info "handoff bundle ready: ${BUNDLE}"
info "review before sharing; bundle contains the handoff report only, not customer folders or application logs."
exit "${HANDOFF_STATUS}"
