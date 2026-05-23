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
OFFLINE_UPDATE_PACKAGE="${MEDIA_AUDIT_OFFLINE_UPDATE_PACKAGE:-}"
OFFLINE_UPDATE_PREVIEW="${MEDIA_AUDIT_OFFLINE_UPDATE_PREVIEW:-}"
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

  echo "## Offline Update Package Inventory"
  if bash scripts/debian-vm-offline-update-inventory.sh --verify-manifests; then
    echo "offline_update_inventory_exit=0"
  else
    STATUS=$?
    echo "offline_update_inventory_exit=${STATUS}"
    EXIT_CODE=1
  fi
  echo

  echo "## Offline Update Preview Inventory"
  if bash scripts/debian-vm-offline-update-preview-inventory.sh --verify-manifests; then
    echo "offline_update_preview_inventory_exit=0"
  else
    STATUS=$?
    echo "offline_update_preview_inventory_exit=${STATUS}"
    EXIT_CODE=1
  fi
  echo

  echo "## Offline Update Preview Verification"
  if [[ -z "${OFFLINE_UPDATE_PREVIEW}" ]]; then
    echo "offline_update_preview=not_provided"
    echo "offline_update_preview_note=set MEDIA_AUDIT_OFFLINE_UPDATE_PREVIEW to verify a preview folder in this report"
  else
    PREVIEW_ARGS=("${OFFLINE_UPDATE_PREVIEW}")
    if [[ -n "${OFFLINE_UPDATE_PACKAGE}" ]]; then
      PREVIEW_ARGS+=("--package" "${OFFLINE_UPDATE_PACKAGE}")
    fi

    if bash scripts/debian-vm-verify-offline-update-preview.sh "${PREVIEW_ARGS[@]}"; then
      echo "offline_update_preview_exit=0"
    else
      STATUS=$?
      echo "offline_update_preview_exit=${STATUS}"
      EXIT_CODE=1
    fi
  fi
  echo

  echo "## Update Plan"
  UPDATE_PLAN_ARGS=()
  if [[ -n "${OFFLINE_UPDATE_PACKAGE}" ]]; then
    UPDATE_PLAN_ARGS+=("--package" "${OFFLINE_UPDATE_PACKAGE}")
  fi
  if [[ -n "${OFFLINE_UPDATE_PREVIEW}" ]]; then
    UPDATE_PLAN_ARGS+=("--preview" "${OFFLINE_UPDATE_PREVIEW}")
  fi

  if bash scripts/debian-vm-offline-update-plan.sh "${UPDATE_PLAN_ARGS[@]}"; then
    echo "offline_update_plan_exit=0"
  else
    STATUS=$?
    echo "offline_update_plan_exit=${STATUS}"
    EXIT_CODE=1
  fi
  echo

  echo "## Offline Update Apply Checklist"
  if [[ -z "${OFFLINE_UPDATE_PACKAGE}" || -z "${OFFLINE_UPDATE_PREVIEW}" ]]; then
    echo "offline_update_apply_checklist=not_provided"
    echo "offline_update_apply_checklist_note=set MEDIA_AUDIT_OFFLINE_UPDATE_PACKAGE and MEDIA_AUDIT_OFFLINE_UPDATE_PREVIEW to include this checklist"
  else
    if bash scripts/debian-vm-offline-update-apply-checklist.sh --package "${OFFLINE_UPDATE_PACKAGE}" --preview "${OFFLINE_UPDATE_PREVIEW}"; then
      echo "offline_update_apply_checklist_exit=0"
    else
      STATUS=$?
      echo "offline_update_apply_checklist_exit=${STATUS}"
      EXIT_CODE=1
    fi
  fi
  echo

  echo "## Online Update Plan"
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
  echo "- Confirm offline update packages and manifests are verified before offline maintenance."
  echo "- Confirm offline update preview inventory is reviewed before offline maintenance."
  echo "- Confirm offline update preview manifests are verified before offline maintenance."
  echo "- Confirm offline update apply checklist is reviewed before any future application workflow."
  echo "- Confirm any warnings are resolved or documented."
  echo "- Review this report before sharing it outside the customer site."
} >"${REPORT}"

info "maintenance report ready: ${REPORT}"
info "review before sharing; report excludes application logs and customer file contents."
exit "${EXIT_CODE}"
