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

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"
command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v find >/dev/null 2>&1 || fail "find is required before running this script"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v sort >/dev/null 2>&1 || fail "sort is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"
command -v tail >/dev/null 2>&1 || fail "tail is required before running this script"
command -v tar >/dev/null 2>&1 || fail "tar is required before running this script"

SUPPORT_DIR="${MEDIA_AUDIT_SUPPORT_DIR:-reports/support}"
BUNDLE_DIR="${MEDIA_AUDIT_SUPPORT_BUNDLE_DIR:-${SUPPORT_DIR}}"
mkdir -p "${SUPPORT_DIR}" "${BUNDLE_DIR}"
[[ -w "${SUPPORT_DIR}" ]] || fail "${SUPPORT_DIR} is not writable by the current user"
[[ -w "${BUNDLE_DIR}" ]] || fail "${BUNDLE_DIR} is not writable by the current user"

info "generating fresh diagnostics report"
MEDIA_AUDIT_SUPPORT_DIR="${SUPPORT_DIR}" bash scripts/debian-vm-diagnostics.sh

LATEST_REPORT="$(
  find "${SUPPORT_DIR}" -maxdepth 1 -type f -name 'media-audit-diagnostics-*.txt' -print \
    | sort \
    | tail -n 1
)"
[[ -n "${LATEST_REPORT}" ]] || fail "no diagnostics report was generated"
REPORT_NAME="$(basename "${LATEST_REPORT}")"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BUNDLE="${BUNDLE_DIR}/media-audit-support-${TIMESTAMP}.tgz"

info "writing support bundle ${BUNDLE}"
tar -czf "${BUNDLE}" -C "${SUPPORT_DIR}" "${REPORT_NAME}"

BUNDLE_MANIFEST="${BUNDLE}.manifest.txt"
BUNDLE_SHA256="$(sha256sum "${BUNDLE}" | awk '{print $1}')"
BUNDLE_SIZE_BYTES="$(stat -c '%s' "${BUNDLE}")"
BUNDLE_NAME="$(basename "${BUNDLE}")"

info "writing support bundle manifest ${BUNDLE_MANIFEST}"
cat >"${BUNDLE_MANIFEST}" <<EOF
# MEDIA Security Audit VM Bundle Manifest
generated_at_utc=${TIMESTAMP}
bundle=${BUNDLE_NAME}
size_bytes=${BUNDLE_SIZE_BYTES}
sha256=${BUNDLE_SHA256}
source_report=${REPORT_NAME}
contents=diagnostics_report_only
EOF

info "support bundle ready: ${BUNDLE}"
info "support bundle manifest ready: ${BUNDLE_MANIFEST}"
info "review before sharing; bundle contains diagnostics only, not customer folders or application logs."
