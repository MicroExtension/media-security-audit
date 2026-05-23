#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-offline-update-apply-checklist.sh --package <package.tgz> --preview <preview-dir> [--manifest <manifest.txt>]

Builds a read-only checklist for a future offline update application workflow.
This script verifies package and preview metadata, then runs the offline update
plan. It does not apply packages, extract archives, replace files, build
images, restart services, collect logs, or run scanners.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

PACKAGE=""
PREVIEW=""
MANIFEST=""

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --package)
      [[ "$#" -ge 2 ]] || fail "--package requires a path"
      PACKAGE="$2"
      shift 2
      ;;
    --package=*)
      PACKAGE="${1#--package=}"
      shift
      ;;
    --preview)
      [[ "$#" -ge 2 ]] || fail "--preview requires a folder"
      PREVIEW="$2"
      shift 2
      ;;
    --preview=*)
      PREVIEW="${1#--preview=}"
      shift
      ;;
    --manifest)
      [[ "$#" -ge 2 ]] || fail "--manifest requires a path"
      MANIFEST="$2"
      shift 2
      ;;
    --manifest=*)
      MANIFEST="${1#--manifest=}"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ -n "${PACKAGE}" ]] || {
  usage
  exit 2
}
[[ -n "${PREVIEW}" ]] || {
  usage
  exit 2
}

command -v date >/dev/null 2>&1 || fail "date is required before running this script"

[[ -f "${PACKAGE}" ]] || fail "offline update package not found: ${PACKAGE}"
[[ -d "${PREVIEW}" ]] || fail "offline update preview folder not found: ${PREVIEW}"

info "building offline update apply checklist only; no package is applied"
printf 'generated_at_utc=%s\n' "$(date -u +%Y%m%dT%H%M%SZ)"
printf 'package=%s\n' "${PACKAGE}"
printf 'preview=%s\n' "${PREVIEW}"

VERIFY_PACKAGE_ARGS=("${PACKAGE}")
PLAN_ARGS=("--package" "${PACKAGE}" "--preview" "${PREVIEW}")
if [[ -n "${MANIFEST}" ]]; then
  VERIFY_PACKAGE_ARGS+=("${MANIFEST}")
  PLAN_ARGS+=("--manifest" "${MANIFEST}")
fi

info "verifying offline update package manifest"
bash scripts/debian-vm-verify-offline-update-package.sh "${VERIFY_PACKAGE_ARGS[@]}"
printf 'package_verification=ready\n'

info "verifying offline update preview manifest"
bash scripts/debian-vm-verify-offline-update-preview.sh "${PREVIEW}" --package "${PACKAGE}"
printf 'preview_verification=ready\n'

info "running read-only offline update plan"
bash scripts/debian-vm-offline-update-plan.sh "${PLAN_ARGS[@]}"
printf 'offline_update_plan=reviewed\n'

printf '\n'
cat <<'CHECKLIST'
Offline update apply checklist:
- Confirm written customer authorization and internal change reference.
- Confirm approved maintenance window and rollback owner.
- Confirm local backup archive and sidecar manifest were verified.
- Confirm offline package manifest was verified.
- Confirm offline preview manifest was verified.
- Confirm maintenance report was reviewed before customer-impacting work.
- Confirm future package application remains explicitly not implemented.

application=not_implemented
live_replacement=not_performed
service_restart=not_performed
scanner_execution=not_performed
CHECKLIST

info "offline update apply checklist complete; no package was applied."
