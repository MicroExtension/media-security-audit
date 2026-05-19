#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

BLOCKED=0
WARNINGS=0

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

env_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key {value=substr($0, length(key) + 2)} END {print value}' ".env"
}

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"

info "reviewing local VM security posture without printing secrets"

if [[ ! -f ".env" ]]; then
  record blocked ".env" "missing; run scripts/debian-vm-init-env.sh before customer use"
else
  ENV_MODE="$(stat -c '%a' ".env")"
  case "${ENV_MODE}" in
    400|600) record ready ".env permissions" ".env mode is ${ENV_MODE}" ;;
    *) record warning ".env permissions" ".env mode is ${ENV_MODE}; prefer 600 for customer VMs" ;;
  esac

  REQUIRE_AUTH="$(env_value MEDIA_AUDIT_REQUIRE_AUTH)"
  if [[ "${REQUIRE_AUTH}" == "true" ]]; then
    record ready "Web authentication" "MEDIA_AUDIT_REQUIRE_AUTH is enabled"
  else
    record blocked "Web authentication" "set MEDIA_AUDIT_REQUIRE_AUTH=true before customer use"
  fi

  WEB_PASSWORD="$(env_value MEDIA_AUDIT_WEB_PASSWORD)"
  if [[ "${#WEB_PASSWORD}" -ge 16 ]]; then
    record ready "Web password" "MEDIA_AUDIT_WEB_PASSWORD is present and not printed"
  else
    record blocked "Web password" "rotate or set a strong MEDIA_AUDIT_WEB_PASSWORD"
  fi

  BIND_ADDRESS="$(env_value MEDIA_AUDIT_BIND)"
  case "${BIND_ADDRESS}" in
    ""|127.0.0.1)
      record ready "Bind address" "UI is local-only"
      ;;
    0.0.0.0)
      record warning "Bind address" "LAN exposure requires a VM firewall or VPN"
      ;;
    *)
      record warning "Bind address" "custom bind address requires documented access control"
      ;;
  esac
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  if docker compose config --quiet >/dev/null 2>&1; then
    record ready "Docker Compose" "configuration is valid"
  else
    record blocked "Docker Compose" "configuration validation failed"
  fi
else
  record blocked "Docker Compose" "docker compose v2 is required before customer use"
fi

if [[ "${BLOCKED}" -gt 0 ]]; then
  info "security review blocked: ${BLOCKED} blocked item(s), ${WARNINGS} warning(s)"
  exit 1
fi

if [[ "${WARNINGS}" -gt 0 ]]; then
  info "security review completed with ${WARNINGS} warning(s); document them before handoff"
else
  info "security review ready"
fi
