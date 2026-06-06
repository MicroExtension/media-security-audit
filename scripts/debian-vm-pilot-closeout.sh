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

command -v date >/dev/null 2>&1 || fail "date is required before running this script"

CLOSEOUT_DIR="${MEDIA_AUDIT_PILOT_CLOSEOUT_DIR:-reports/pilot-closeout}"
READINESS_DIR="${MEDIA_AUDIT_V1_READINESS_DIR:-reports/v1-readiness}"
mkdir -p "${CLOSEOUT_DIR}"
[[ -w "${CLOSEOUT_DIR}" ]] || fail "${CLOSEOUT_DIR} is not writable by the current user"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="${CLOSEOUT_DIR}/media-audit-pilot-closeout-${TIMESTAMP}.txt"
EXIT_CODE=0

latest_file() {
  local directory="$1"
  local pattern="$2"

  [[ -d "${directory}" ]] || return 0

  find "${directory}" -maxdepth 1 -type f -name "${pattern}" -printf '%T@ %p\n' 2>/dev/null \
    | sort -nr \
    | awk 'NR == 1 {print $2}'
}

run_section() {
  local label="$1"
  shift

  echo "## ${label}"
  if "$@"; then
    printf '%s_exit=0\n' "$(echo "${label}" | tr '[:upper:] ' '[:lower:]_')"
  else
    STATUS=$?
    printf '%s_exit=%s\n' "$(echo "${label}" | tr '[:upper:] ' '[:lower:]_')" "${STATUS}"
    EXIT_CODE=1
  fi
  echo
}

info "writing pilot closeout report ${REPORT}"

{
  echo "# MEDIA Security Audit V1 Pilot Closeout"
  echo "generated_at_utc=${TIMESTAMP}"
  echo "scanner_execution=not_performed"
  echo "package_installation=not_performed"
  echo "application_logs=not_collected"
  echo "customer_file_contents=not_collected"
  echo

  run_section "V1 Readiness Report" bash scripts/debian-vm-v1-readiness-report.sh
  run_section "Handoff Bundle" bash scripts/debian-vm-handoff-bundle.sh
  run_section "Bundle Inventory" bash scripts/debian-vm-bundle-inventory.sh --verify-manifests

  echo "## Generated Evidence"
  LATEST_READINESS="$(latest_file "${READINESS_DIR}" 'media-audit-v1-readiness-*.txt')"
  if [[ -n "${LATEST_READINESS}" ]]; then
    printf 'latest_v1_readiness_report=%s\n' "${LATEST_READINESS}"
    READINESS_VALUE="$(grep -E '^v1_readiness=' "${LATEST_READINESS}" | tail -n 1 | cut -d= -f2- || true)"
    printf 'latest_v1_readiness=%s\n' "${READINESS_VALUE:-missing}"
    if [[ "${READINESS_VALUE:-}" != "ready" ]]; then
      EXIT_CODE=1
    fi
  else
    echo "latest_v1_readiness_report=missing"
    echo "latest_v1_readiness=missing"
    EXIT_CODE=1
  fi

  LATEST_HANDOFF_BUNDLE="$(latest_file "reports/handoff/bundles" 'media-audit-handoff-*.tgz')"
  if [[ -n "${LATEST_HANDOFF_BUNDLE}" ]]; then
    printf 'latest_handoff_bundle=%s\n' "${LATEST_HANDOFF_BUNDLE}"
    if [[ -f "${LATEST_HANDOFF_BUNDLE}.manifest.txt" ]]; then
      echo "latest_handoff_bundle_manifest=present"
    else
      echo "latest_handoff_bundle_manifest=missing"
      EXIT_CODE=1
    fi
  else
    echo "latest_handoff_bundle=missing"
    echo "latest_handoff_bundle_manifest=missing"
    EXIT_CODE=1
  fi
  echo

  echo "## Technician Acceptance"
  echo "- Confirm the latest V1 readiness report is ready."
  echo "- Confirm the handoff bundle manifest is present and verified."
  echo "- Confirm web authentication remains enabled and the password is vaulted."
  echo "- Confirm the UI is local-only or protected by approved firewall or VPN controls."
  echo "- Confirm mission authorization, approved scope, reports, and export package were reviewed."
  echo "- Confirm any live checks were performed only after written authorization and approved scope."
  echo "- Confirm no application logs or customer file contents are included in this closeout report."
  echo

  if [[ "${EXIT_CODE}" -eq 0 ]]; then
    echo "pilot_closeout=ready"
  else
    echo "pilot_closeout=blocked"
  fi
} >"${REPORT}"

info "pilot closeout report ready: ${REPORT}"
info "review before customer handoff; report excludes application logs and customer file contents."
exit "${EXIT_CODE}"
