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

MAINTENANCE_DIR="${MEDIA_AUDIT_MAINTENANCE_DIR:-reports/maintenance}"
mkdir -p "${MAINTENANCE_DIR}"
[[ -w "${MAINTENANCE_DIR}" ]] || fail "${MAINTENANCE_DIR} is not writable by the current user"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="${MAINTENANCE_DIR}/media-audit-maintenance-${TIMESTAMP}.txt"
EXIT_CODE=0

info "writing VM maintenance report ${REPORT}"

{
  echo "# MEDIA Security Audit VM Maintenance Report"
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

  echo "## Backup Inventory"
  if bash scripts/debian-vm-backup-inventory.sh --verify-manifests; then
    echo "backup_inventory_exit=0"
  else
    STATUS=$?
    echo "backup_inventory_exit=${STATUS}"
    EXIT_CODE=1
  fi
  echo

  echo "## Bundle Inventory"
  if bash scripts/debian-vm-bundle-inventory.sh --verify-manifests; then
    echo "bundle_inventory_exit=0"
  else
    STATUS=$?
    echo "bundle_inventory_exit=${STATUS}"
    EXIT_CODE=1
  fi
  echo

  echo "## Update Plan"
  if bash scripts/debian-vm-update-plan.sh; then
    echo "update_plan_exit=0"
  else
    STATUS=$?
    echo "update_plan_exit=${STATUS}"
    EXIT_CODE=1
  fi
  echo

  echo "## Technician Review"
  echo "- Confirm the maintenance window is approved."
  echo "- Confirm customer authorization and internal change reference."
  echo "- Confirm backup archive and manifest verification before updating."
  echo "- Confirm shareable bundles and manifests are verified before handoff."
  echo "- Confirm any warnings are resolved or documented."
  echo "- Review this report before sharing it outside the customer site."
} >"${REPORT}"

info "maintenance report ready: ${REPORT}"
info "review before sharing; report excludes application logs and customer file contents."
exit "${EXIT_CODE}"
