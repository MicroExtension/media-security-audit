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

RELEASE_DIR="${MEDIA_AUDIT_RELEASE_CANDIDATE_DIR:-reports/release-candidate}"
CLOSEOUT_DIR="${MEDIA_AUDIT_PILOT_CLOSEOUT_DIR:-reports/pilot-closeout}"
READINESS_DIR="${MEDIA_AUDIT_V1_READINESS_DIR:-reports/v1-readiness}"
HANDOFF_DIR="${MEDIA_AUDIT_HANDOFF_DIR:-reports/handoff}"
HANDOFF_BUNDLE_DIR="${MEDIA_AUDIT_HANDOFF_BUNDLE_DIR:-${HANDOFF_DIR}}"
mkdir -p "${RELEASE_DIR}"
[[ -w "${RELEASE_DIR}" ]] || fail "${RELEASE_DIR} is not writable by the current user"
export MEDIA_AUDIT_PILOT_CLOSEOUT_DIR="${CLOSEOUT_DIR}"
export MEDIA_AUDIT_V1_READINESS_DIR="${READINESS_DIR}"
export MEDIA_AUDIT_HANDOFF_DIR="${HANDOFF_DIR}"
export MEDIA_AUDIT_HANDOFF_BUNDLE_DIR="${HANDOFF_BUNDLE_DIR}"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="${RELEASE_DIR}/media-audit-v1-release-candidate-${TIMESTAMP}.txt"
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

status_value() {
  local file="$1"
  local key="$2"

  grep -E "^${key}=" "${file}" | tail -n 1 | cut -d= -f2- || true
}

info "writing V1 release candidate report ${REPORT}"

{
  echo "# MEDIA Security Audit V1 Release Candidate"
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

  run_section "Pilot Closeout" bash scripts/debian-vm-pilot-closeout.sh
  run_section "Bundle Inventory" bash scripts/debian-vm-bundle-inventory.sh --verify-manifests

  echo "## Release Candidate Evidence"
  LATEST_CLOSEOUT="$(latest_file "${CLOSEOUT_DIR}" 'media-audit-pilot-closeout-*.txt')"
  if [[ -n "${LATEST_CLOSEOUT}" ]]; then
    printf 'latest_pilot_closeout_report=%s\n' "${LATEST_CLOSEOUT}"
    CLOSEOUT_VALUE="$(status_value "${LATEST_CLOSEOUT}" pilot_closeout)"
    printf 'latest_pilot_closeout=%s\n' "${CLOSEOUT_VALUE:-missing}"
    if [[ "${CLOSEOUT_VALUE:-}" != "ready" ]]; then
      EXIT_CODE=1
    fi
  else
    echo "latest_pilot_closeout_report=missing"
    echo "latest_pilot_closeout=missing"
    EXIT_CODE=1
  fi

  LATEST_READINESS="$(latest_file "${READINESS_DIR}" 'media-audit-v1-readiness-*.txt')"
  if [[ -n "${LATEST_READINESS}" ]]; then
    printf 'latest_v1_readiness_report=%s\n' "${LATEST_READINESS}"
    READINESS_VALUE="$(status_value "${LATEST_READINESS}" v1_readiness)"
    printf 'latest_v1_readiness=%s\n' "${READINESS_VALUE:-missing}"
    if [[ "${READINESS_VALUE:-}" != "ready" ]]; then
      EXIT_CODE=1
    fi
  else
    echo "latest_v1_readiness_report=missing"
    echo "latest_v1_readiness=missing"
    EXIT_CODE=1
  fi

  LATEST_HANDOFF_BUNDLE="$(latest_file "${HANDOFF_BUNDLE_DIR}" 'media-audit-handoff-*.tgz')"
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

  echo "## Release Candidate Acceptance"
  echo "- Confirm the VM is on branch main with no tracked local changes."
  echo "- Confirm latest_v1_readiness=ready and latest_pilot_closeout=ready."
  echo "- Confirm the latest handoff bundle and sidecar manifest are present and verified."
  echo "- Confirm web authentication remains enabled and the password is vaulted."
  echo "- Confirm the UI is local-only or protected by approved firewall or VPN controls."
  echo "- Confirm first customer missions require written authorization and approved scope."
  echo "- Confirm optional missing tooling is documented before live checks."
  echo "- Confirm no scanner was executed by this release candidate report."
  echo "- Confirm this report is archived with the VM pilot evidence."
  echo

  if [[ "${EXIT_CODE}" -eq 0 ]]; then
    echo "release_candidate=ready"
  else
    echo "release_candidate=blocked"
  fi
} >"${REPORT}"

info "V1 release candidate report ready: ${REPORT}"
info "review before declaring the VM ready for a customer pilot; report excludes logs and customer file contents."
exit "${EXIT_CODE}"
