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

HANDOFF_DIR="${MEDIA_AUDIT_HANDOFF_DIR:-reports/handoff}"
mkdir -p "${HANDOFF_DIR}"
[[ -w "${HANDOFF_DIR}" ]] || fail "${HANDOFF_DIR} is not writable by the current user"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="${HANDOFF_DIR}/media-audit-handoff-${TIMESTAMP}.txt"
EXIT_CODE=0

info "writing VM handoff report ${REPORT}"

{
  echo "# MEDIA Security Audit VM Handoff Report"
  echo "generated_at_utc=${TIMESTAMP}"
  echo

  echo "## Security Review"
  if bash scripts/debian-vm-security-review.sh; then
    echo "security_review_exit=0"
  else
    STATUS=$?
    echo "security_review_exit=${STATUS}"
    EXIT_CODE=1
  fi
  echo

  echo "## Deployment Status"
  if bash scripts/debian-vm-status.sh; then
    echo "deployment_status_exit=0"
  else
    STATUS=$?
    echo "deployment_status_exit=${STATUS}"
    EXIT_CODE=1
  fi
  echo

  echo "## Technician Review"
  echo "- Confirm customer authorization and approved administration subnet."
  echo "- Confirm MEDIA_AUDIT_REQUIRE_AUTH remains enabled."
  echo "- Confirm any LAN exposure is protected by firewall or VPN."
  echo "- Store the current web password in the maintenance password vault."
  echo "- Review this report before sharing it outside the customer site."
} >"${REPORT}"

info "handoff report ready: ${REPORT}"
info "review before sharing; report excludes application logs and customer file contents."
exit "${EXIT_CODE}"
