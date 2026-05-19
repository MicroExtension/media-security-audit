#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-firewall-plan.sh --admin-cidr CIDR

Prints a firewall change plan for controlled LAN access to the local web UI.
No firewall command is executed by this helper.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

env_value() {
  local key="$1"
  [[ -f ".env" ]] || return 0
  awk -F= -v key="${key}" '$1 == key {value=substr($0, length(key) + 2)} END {print value}' ".env"
}

ADMIN_CIDR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --admin-cidr)
      ADMIN_CIDR="${2:-}"
      shift 2
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

[[ -n "${ADMIN_CIDR}" ]] || {
  usage
  fail "--admin-cidr is required"
}
[[ "${ADMIN_CIDR}" =~ ^[0-9A-Fa-f:.]+/[0-9]{1,3}$ ]] || fail "--admin-cidr must use CIDR notation"

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"

BIND_ADDRESS="$(env_value MEDIA_AUDIT_BIND)"
PORT="$(env_value MEDIA_AUDIT_PORT)"
BIND_ADDRESS="${BIND_ADDRESS:-127.0.0.1}"
PORT="${PORT:-8080}"
[[ "${PORT}" =~ ^[0-9]+$ ]] || fail "MEDIA_AUDIT_PORT must be numeric"
(( PORT >= 1 && PORT <= 65535 )) || fail "MEDIA_AUDIT_PORT must be between 1 and 65535"

info "firewall plan only; no command is executed"
printf 'Current bind address: %s\n' "${BIND_ADDRESS}"
printf 'Web UI port: %s\n' "${PORT}"
printf 'Approved admin CIDR: %s\n' "${ADMIN_CIDR}"
printf '\n'

if [[ "${BIND_ADDRESS}" != "0.0.0.0" ]]; then
  printf '[warning] MEDIA_AUDIT_BIND is not 0.0.0.0; LAN access also requires updating .env and restarting during maintenance.\n'
fi

cat <<PLAN
Review before applying on the VM console:
1. Confirm management access will not be locked out.
2. Confirm customer authorization allows LAN administration access.
3. Confirm MEDIA_AUDIT_REQUIRE_AUTH remains true.
4. Apply a host firewall or VPN rule that allows only the approved admin CIDR.

Example UFW commands to review, not executed:
  ufw allow from ${ADMIN_CIDR} to any port ${PORT} proto tcp comment 'MEDIA Security Audit Web UI'
  ufw status numbered

After firewall approval:
  bash scripts/debian-vm-security-review.sh
  bash scripts/debian-vm-restart.sh --confirm
PLAN
