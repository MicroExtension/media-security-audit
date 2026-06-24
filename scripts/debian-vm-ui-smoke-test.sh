#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

REPORT_DIR="${MEDIA_AUDIT_UI_SMOKE_DIR:-reports/test-readiness}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="${REPORT_DIR}/media-audit-ui-smoke-test-${TIMESTAMP}.txt"
READY=0
WARNINGS=0
BLOCKED=0

mkdir -p "${REPORT_DIR}"

info() {
  printf '[media-audit] %s\n' "$1"
}

record() {
  local status="$1"
  local label="$2"
  local detail="$3"

  printf '[%s] %s - %s\n' "${status}" "${label}" "${detail}"
  case "${status}" in
    ready) READY=$((READY + 1)) ;;
    warning) WARNINGS=$((WARNINGS + 1)) ;;
    blocked) BLOCKED=$((BLOCKED + 1)) ;;
  esac
}

env_value() {
  local key="$1"
  if [[ ! -f ".env" ]]; then
    return 0
  fi
  awk -F= -v key="${key}" '$1 == key {value=substr($0, length(key) + 2)} END {print value}' ".env"
}

{
  echo "# MEDIA Security Audit VM UI Smoke Test"
  echo "generated_at_utc=${TIMESTAMP}"
  echo "scanner_execution=not_performed"
  echo "package_installation=not_performed"
  echo "application_logs=not_collected"
  echo "customer_file_contents=not_collected"
  echo

  echo "## Repository"
  if command -v git >/dev/null 2>&1; then
    BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    if [[ -n "${BRANCH}" ]]; then
      record ready "git branch" "current branch is ${BRANCH}"
      echo "branch=${BRANCH}"
    else
      record warning "git branch" "unable to determine current branch"
      echo "branch=unknown"
    fi

    TRACKED_CHANGES="$(git status --short --untracked-files=no 2>/dev/null || true)"
    if [[ -z "${TRACKED_CHANGES}" ]]; then
      record ready "tracked changes" "no tracked local changes"
      echo "tracked_changes=ready"
    else
      record warning "tracked changes" "tracked local changes are present"
      echo "tracked_changes=warning"
    fi
  else
    record blocked "git" "git is required to verify the deployed branch"
    echo "branch=missing"
    echo "tracked_changes=blocked"
  fi
  echo

  echo "## Environment"
  if [[ -f ".env" ]]; then
    record ready ".env" "environment file is present"
    echo "env_file=present"
  else
    record blocked ".env" "run scripts/debian-vm-init-env.sh before testing the UI"
    echo "env_file=missing"
  fi

  REQUIRE_AUTH="$(env_value MEDIA_AUDIT_REQUIRE_AUTH)"
  if [[ "${REQUIRE_AUTH}" == "true" ]]; then
    record ready "web auth" "MEDIA_AUDIT_REQUIRE_AUTH is enabled"
    echo "web_auth=enabled"
  else
    record blocked "web auth" "set MEDIA_AUDIT_REQUIRE_AUTH=true before customer testing"
    echo "web_auth=blocked"
  fi

  WEB_PASSWORD="$(env_value MEDIA_AUDIT_WEB_PASSWORD)"
  if [[ "${#WEB_PASSWORD}" -ge 16 ]]; then
    record ready "web password" "password is present and not printed"
    echo "web_password=configured"
  else
    record blocked "web password" "rotate or set a strong MEDIA_AUDIT_WEB_PASSWORD"
    echo "web_password=blocked"
  fi

  BIND_ADDRESS="$(env_value MEDIA_AUDIT_BIND)"
  PORT="$(env_value MEDIA_AUDIT_PORT)"
  [[ -n "${BIND_ADDRESS}" ]] || BIND_ADDRESS="127.0.0.1"
  [[ -n "${PORT}" ]] || PORT="8080"
  echo "bind_address=${BIND_ADDRESS}"
  echo "port=${PORT}"
  case "${BIND_ADDRESS}" in
    127.0.0.1)
      record ready "bind address" "UI is local-only; use SSH port forwarding for workstation access"
      ;;
    0.0.0.0)
      record warning "bind address" "LAN exposure requires firewall or VPN control"
      ;;
    *)
      record warning "bind address" "custom bind address requires documented access control"
      ;;
  esac
  echo

  echo "## Compose"
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    record ready "docker compose" "Docker Compose v2 is available"
    if docker compose config --quiet >/dev/null 2>&1; then
      record ready "compose config" "configuration is valid"
      echo "compose_config=ready"
    else
      record blocked "compose config" "configuration validation failed"
      echo "compose_config=blocked"
    fi

    COMPOSE_PS="$(docker compose ps 2>/dev/null || true)"
    echo "${COMPOSE_PS}"
    if printf '%s\n' "${COMPOSE_PS}" | grep -Eq 'media-security-audit|media-audit'; then
      record ready "compose service" "media-audit service is present in Compose status"
      echo "compose_service=present"
    else
      record warning "compose service" "media-audit service is not visible; start with scripts/debian-vm-start.sh"
      echo "compose_service=missing"
    fi
  else
    record blocked "docker compose" "Docker Compose v2 is required before UI testing"
    echo "compose_config=blocked"
    echo "compose_service=blocked"
  fi
  echo

  echo "## Local HTTP"
  if command -v curl >/dev/null 2>&1; then
    HTTP_STATUS="$(curl -fsS -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:${PORT}/test-readiness" 2>/dev/null || true)"
    if [[ "${HTTP_STATUS}" == "200" || "${HTTP_STATUS}" == "401" ]]; then
      record ready "local web endpoint" "HTTP status ${HTTP_STATUS} from /test-readiness"
      echo "local_http=ready"
      echo "local_http_status=${HTTP_STATUS}"
    elif [[ -n "${HTTP_STATUS}" ]]; then
      record warning "local web endpoint" "HTTP status ${HTTP_STATUS}; review service status"
      echo "local_http=warning"
      echo "local_http_status=${HTTP_STATUS}"
    else
      record blocked "local web endpoint" "no response from http://127.0.0.1:${PORT}/test-readiness"
      echo "local_http=blocked"
      echo "local_http_status=missing"
    fi
  else
    record warning "curl" "curl is not installed; browser test remains manual"
    echo "local_http=not_checked"
  fi
  echo

  echo "## Guarded Reviews"
  set +e
  bash scripts/debian-vm-security-review.sh
  SECURITY_REVIEW_EXIT=$?
  bash scripts/debian-vm-status.sh
  STATUS_REVIEW_EXIT=$?
  set -e
  echo "security_review_exit=${SECURITY_REVIEW_EXIT}"
  echo "deployment_status_exit=${STATUS_REVIEW_EXIT}"
  if [[ "${SECURITY_REVIEW_EXIT}" -eq 0 ]]; then
    record ready "security review" "security review returned 0"
  else
    record blocked "security review" "fix security review blockers before customer testing"
  fi
  if [[ "${STATUS_REVIEW_EXIT}" -eq 0 ]]; then
    record ready "deployment status" "status helper returned 0"
  else
    record warning "deployment status" "review status helper output above"
  fi
  echo

  echo "## Browser Checklist"
  echo "- Open http://127.0.0.1:${PORT}/test-readiness through SSH forwarding."
  echo "- Confirm login with the vaulted web password."
  echo "- Create or review one pilot client."
  echo "- Create a guided audit with approved scope and selected services."
  echo "- Open the audit console and verify progress, CVE/KEV review, reports, and exports."
  echo "- Record feedback for screens that are still too dense or unclear."
  echo

  echo "ready_count=${READY}"
  echo "warning_count=${WARNINGS}"
  echo "blocked_count=${BLOCKED}"
  if [[ "${BLOCKED}" -gt 0 ]]; then
    echo "ui_smoke_test=blocked"
  elif [[ "${WARNINGS}" -gt 0 ]]; then
    echo "ui_smoke_test=warning"
  else
    echo "ui_smoke_test=ready"
  fi
} > "${REPORT}"

info "UI smoke test report ready: ${REPORT}"
info "review before customer testing; report excludes secrets, application logs, and customer file contents."

if grep -q '^ui_smoke_test=blocked$' "${REPORT}"; then
  exit 1
fi
