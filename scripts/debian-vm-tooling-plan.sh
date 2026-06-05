#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

BLOCKED=0
WARNINGS=0
STRICT=false
INCLUDE_NUCLEI=false

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-tooling-plan.sh [--strict] [--include-nuclei]

Reviews host-visible VM tool availability and prints installation commands for
technician approval. Default mode is advisory because the Docker deployment
preflight is the source of truth for runtime tool availability. No package
command, scanner, template update, or Docker command is executed by this helper.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

record() {
  local status="$1"
  local label="$2"
  local detail="$3"

  printf '[%s] %s - %s\n' "${status}" "${label}" "${detail}"
  case "${status}" in
    blocked) BLOCKED=$((BLOCKED + 1)) ;;
    warning) WARNINGS=$((WARNINGS + 1)) ;;
  esac
}

tool_status() {
  local command_name="$1"
  local label="$2"
  local missing_status="$3"
  local missing_detail="$4"

  if command -v "${command_name}" >/dev/null 2>&1; then
    record ready "${label}" "found at $(command -v "${command_name}")"
  else
    record "${missing_status}" "${label}" "${missing_detail}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict)
      STRICT=true
      shift
      ;;
    --include-nuclei)
      INCLUDE_NUCLEI=true
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      usage
      fail "unknown argument: $1"
      ;;
  esac
done

info "tooling plan only; no package command is executed"

tool_status "nmap" "Nmap" "blocked" "required before guarded Nmap execution"
tool_status "smbclient" "smbclient" "blocked" "required before guarded SMB execution"
tool_status "ldapsearch" "ldapsearch" "blocked" "required before guarded LDAP execution"
tool_status "testssl.sh" "testssl.sh" "warning" "required only before TLS live checks"

if [[ "${INCLUDE_NUCLEI}" == "true" ]]; then
  tool_status "nuclei" "Nuclei" "warning" "future module only; install after template governance is approved"
else
  if command -v nuclei >/dev/null 2>&1; then
    record ready "Nuclei" "found at $(command -v nuclei)"
  else
    record warning "Nuclei" "future optional; use --include-nuclei only when the module is approved"
  fi
fi

printf '\n'
cat <<'PLAN'
Reviewed commands, not executed by this helper:
  sudo apt update
  sudo apt install -y nmap smbclient ldap-utils
  sudo apt install -y testssl.sh

After installing pilot or TLS tools:
  bash scripts/debian-vm-preflight.sh
  bash scripts/debian-vm-security-review.sh

Use strict preflight only when every warning is intentionally resolved:
  bash scripts/debian-vm-preflight.sh --strict

Nuclei remains future optional for V1:
  - install it only when the Nuclei module is enabled
  - use an approved pinned package or release process
  - keep templates governed, reviewed, and versioned before customer use
  - do not run template updates during an audit without authorization
PLAN

if [[ "${STRICT}" == "true" && $((BLOCKED + WARNINGS)) -gt 0 ]]; then
  info "tooling plan strict mode failed: ${BLOCKED} required host tool gap(s), ${WARNINGS} warning(s)"
  exit 1
fi

if [[ "${BLOCKED}" -gt 0 ]]; then
  info "tooling plan completed with ${BLOCKED} host tool gap(s); Docker preflight remains the runtime readiness gate"
fi

if [[ "${WARNINGS}" -gt 0 ]]; then
  info "tooling plan completed with ${WARNINGS} warning(s); resolve or document them before live checks"
else
  info "tooling plan ready"
fi
