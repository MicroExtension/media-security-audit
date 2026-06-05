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
command -v git >/dev/null 2>&1 || fail "git is required before running this script"

READINESS_DIR="${MEDIA_AUDIT_V1_READINESS_DIR:-reports/v1-readiness}"
mkdir -p "${READINESS_DIR}"
[[ -w "${READINESS_DIR}" ]] || fail "${READINESS_DIR} is not writable by the current user"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="${READINESS_DIR}/media-audit-v1-readiness-${TIMESTAMP}.txt"
EXIT_CODE=0

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

info "writing V1 readiness report ${REPORT}"

{
  echo "# MEDIA Security Audit V1 Readiness Report"
  echo "generated_at_utc=${TIMESTAMP}"
  echo "scanner_execution=not_performed"
  echo "package_installation=not_performed"
  echo "application_logs=not_collected"
  echo "customer_file_contents=not_collected"
  echo

  echo "## Git Snapshot"
  CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  CURRENT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
  printf 'branch=%s\n' "${CURRENT_BRANCH}"
  printf 'commit=%s\n' "${CURRENT_COMMIT}"
  if [[ "${CURRENT_BRANCH}" == "main" ]]; then
    echo "branch_status=ready"
  else
    echo "branch_status=blocked"
    EXIT_CODE=1
  fi
  if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    echo "tracked_changes=blocked"
    EXIT_CODE=1
  else
    echo "tracked_changes=ready"
  fi
  echo

  run_section "Security Review" bash scripts/debian-vm-security-review.sh
  run_section "Tooling Plan" bash scripts/debian-vm-tooling-plan.sh
  run_section "Deployment Status" bash scripts/debian-vm-status.sh
  run_section "Bundle Inventory" bash scripts/debian-vm-bundle-inventory.sh --verify-manifests

  echo "## Pilot Acceptance Review"
  echo "- Confirm the VM is on branch main with no tracked local changes."
  echo "- Confirm web authentication is enabled and the password is vaulted."
  echo "- Confirm the UI is local-only or protected by VPN/firewall."
  echo "- Confirm pilot-required tools are ready or documented before live checks."
  echo "- Confirm missing testssl.sh is documented if TLS live checks are deferred."
  echo "- Confirm Nuclei remains disabled until template governance is approved."
  echo "- Confirm mission authorization, approved scope, reports, and export package are reviewed."
  echo "- Confirm handoff and support bundles are reviewed before sharing."
  echo "- Confirm no scanner was executed by this readiness report."
  echo

  if [[ "${EXIT_CODE}" -eq 0 ]]; then
    echo "v1_readiness=ready"
  else
    echo "v1_readiness=blocked"
  fi
} >"${REPORT}"

info "V1 readiness report ready: ${REPORT}"
info "review before customer pilot; report excludes application logs and customer file contents."
exit "${EXIT_CODE}"
