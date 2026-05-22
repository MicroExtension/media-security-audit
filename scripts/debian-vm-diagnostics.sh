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
command -v docker >/dev/null 2>&1 || fail "docker is required before running this script"
command -v du >/dev/null 2>&1 || fail "du is required before running this script"
docker compose version >/dev/null 2>&1 || fail "docker compose v2 is required before running this script"

SUPPORT_DIR="${MEDIA_AUDIT_SUPPORT_DIR:-reports/support}"
mkdir -p "${SUPPORT_DIR}"
[[ -w "${SUPPORT_DIR}" ]] || fail "${SUPPORT_DIR} is not writable by the current user"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="${SUPPORT_DIR}/media-audit-diagnostics-${TIMESTAMP}.txt"

info "writing VM diagnostics report ${REPORT}"

{
  echo "# MEDIA Security Audit VM Diagnostics"
  echo "generated_at_utc=${TIMESTAMP}"
  echo

  echo "## Git"
  echo "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  echo "commit=$(git rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "tracked_status:"
  git status --short --untracked-files=no 2>/dev/null || true
  echo

  echo "## Docker Compose"
  if docker compose config --quiet >/dev/null 2>&1; then
    echo "compose_config=ready"
  else
    echo "compose_config=blocked"
  fi
  echo "compose_services:"
  docker compose ps 2>/dev/null || true
  echo

  echo "## Persistent Folders"
  for folder in data runs reports evidence; do
    if [[ -d "${folder}" ]]; then
      printf '%s\t%s\n' "${folder}" "$(du -sh "${folder}" 2>/dev/null | cut -f1)"
    else
      printf '%s\tmissing\n' "${folder}"
    fi
  done
  echo

  echo "## Deployment Preflight JSON"
  docker compose run --rm media-audit preflight \
    --data-dir /var/lib/media-audit/data \
    --reports-dir /var/lib/media-audit/reports \
    --format json 2>/dev/null || echo '{"status":"blocked","detail":"preflight command failed"}'
  echo

  echo "## Bundle Inventory"
  if bash scripts/debian-vm-bundle-inventory.sh --verify-manifests; then
    echo "bundle_inventory_exit=0"
  else
    STATUS=$?
    echo "bundle_inventory_exit=${STATUS}"
  fi
} >"${REPORT}"

info "diagnostics report ready: ${REPORT}"
info "review before sharing; it should not contain customer data or application logs."
