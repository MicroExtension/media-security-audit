#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

BLOCKED=0
WARNINGS=0
PACKAGE=""
MANIFEST=""

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

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-offline-update-plan.sh [--package <path>] [--manifest <path>]

Plan an offline update before an approved maintenance window.

This helper is read-only. It does not apply packages, extract archives, pull
from Git, build images, restart services, or run scanners.
USAGE
}

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

command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v cut >/dev/null 2>&1 || fail "cut is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v find >/dev/null 2>&1 || fail "find is required before running this script"
command -v git >/dev/null 2>&1 || fail "git is required before running this script"
command -v grep >/dev/null 2>&1 || fail "grep is required before running this script"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v sort >/dev/null 2>&1 || fail "sort is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"
command -v tail >/dev/null 2>&1 || fail "tail is required before running this script"

info "planning offline update only; no update command is executed"
printf 'generated_at_utc=%s\n' "$(date -u +%Y%m%dT%H%M%SZ)"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
CURRENT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
printf 'current_branch=%s\n' "${CURRENT_BRANCH}"
printf 'current_commit=%s\n' "${CURRENT_COMMIT}"

if [[ "${CURRENT_BRANCH}" == "main" ]]; then
  record ready "Git branch" "VM clone is on main"
else
  record blocked "Git branch" "switch to main before preparing an offline update"
fi

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  record blocked "Tracked changes" "commit, stash, or revert tracked local changes before updating"
else
  record ready "Tracked changes" "no tracked local changes detected"
fi

if [[ ! -f ".env" ]]; then
  record blocked ".env" "missing; run scripts/debian-vm-init-env.sh before updating"
else
  if grep -Eq '^MEDIA_AUDIT_WEB_PASSWORD=.+$' ".env"; then
    record ready "Web password" "MEDIA_AUDIT_WEB_PASSWORD is configured and not printed"
  else
    record blocked "Web password" "set or rotate MEDIA_AUDIT_WEB_PASSWORD before updating"
  fi

  if grep -Eq '^MEDIA_AUDIT_REQUIRE_AUTH=true$' ".env"; then
    record ready "Web authentication" "MEDIA_AUDIT_REQUIRE_AUTH is enabled"
  else
    record warning "Web authentication" "set MEDIA_AUDIT_REQUIRE_AUTH=true before customer use"
  fi
fi

BACKUP_DIR="${MEDIA_AUDIT_BACKUP_DIR:-reports/backups}"
if [[ -d "${BACKUP_DIR}" ]]; then
  LATEST_BACKUP="$(
    find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'media-audit-backup-*.tgz' -print \
      | sort \
      | tail -n 1
  )"
  if [[ -n "${LATEST_BACKUP}" ]]; then
    record ready "Local backup" "latest backup candidate: ${LATEST_BACKUP}"
    if [[ -f "${LATEST_BACKUP}.manifest.txt" ]]; then
      record ready "Backup manifest" "sidecar manifest found for latest backup"
    else
      record warning "Backup manifest" "create and verify a sidecar manifest before updating"
    fi
  else
    record warning "Local backup" "no local backup archive found in ${BACKUP_DIR}"
  fi
else
  record warning "Local backup" "${BACKUP_DIR} does not exist yet"
fi

if [[ -z "${PACKAGE}" ]]; then
  record warning "Offline package" "no package path provided; pass --package when a package is available"
else
  if [[ ! -f "${PACKAGE}" ]]; then
    record blocked "Offline package" "${PACKAGE} was not found"
  else
    PACKAGE_NAME="$(basename "${PACKAGE}")"
    PACKAGE_SIZE_BYTES="$(stat -c '%s' "${PACKAGE}")"
    PACKAGE_SHA256="$(sha256sum "${PACKAGE}" | cut -d' ' -f1)"
    record ready "Offline package" "${PACKAGE_NAME} exists"
    printf 'package_size_bytes=%s\n' "${PACKAGE_SIZE_BYTES}"
    printf 'package_sha256=%s\n' "${PACKAGE_SHA256}"

    PACKAGE_MANIFEST="${MANIFEST:-${PACKAGE}.manifest.txt}"
    if [[ -f "${PACKAGE_MANIFEST}" ]]; then
      record ready "Package manifest" "sidecar manifest found: ${PACKAGE_MANIFEST}"
      MANIFEST_SHA256="$(grep -E '^sha256=' "${PACKAGE_MANIFEST}" | tail -n 1 | cut -d= -f2- || true)"
      MANIFEST_SIZE_BYTES="$(grep -E '^size_bytes=' "${PACKAGE_MANIFEST}" | tail -n 1 | cut -d= -f2- || true)"

      if [[ -n "${MANIFEST_SHA256}" ]]; then
        if [[ "${MANIFEST_SHA256}" == "${PACKAGE_SHA256}" ]]; then
          record ready "Package checksum" "manifest SHA-256 matches package"
        else
          record blocked "Package checksum" "manifest SHA-256 does not match package"
        fi
      else
        record warning "Package checksum" "manifest does not contain sha256="
      fi

      if [[ -n "${MANIFEST_SIZE_BYTES}" ]]; then
        if [[ "${MANIFEST_SIZE_BYTES}" == "${PACKAGE_SIZE_BYTES}" ]]; then
          record ready "Package size" "manifest size matches package"
        else
          record blocked "Package size" "manifest size does not match package"
        fi
      else
        record warning "Package size" "manifest does not contain size_bytes="
      fi
    elif [[ -n "${MANIFEST}" ]]; then
      record blocked "Package manifest" "${MANIFEST} was not found"
    else
      record warning "Package manifest" "no sidecar manifest found at ${PACKAGE_MANIFEST}"
    fi
  fi
fi

printf '\n'
cat <<'PLAN'
Next reviewed commands, not executed by this helper:
  bash scripts/debian-vm-backup.sh
  bash scripts/debian-vm-backup-manifest.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
  bash scripts/debian-vm-verify-backup-manifest.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
  bash scripts/debian-vm-verify-offline-update-package.sh media-audit-offline-update-YYYYMMDDTHHMMSSZ.tgz
  # Copy the verified offline update package and manifest to the VM.
  # Offline package application is not implemented yet.
  bash scripts/debian-vm-preflight.sh
  bash scripts/debian-vm-restart.sh --confirm

Review before offline update:
- Confirm a maintenance window is approved.
- Confirm the latest backup archive and manifest were verified.
- Confirm the offline package source, checksum, and size are approved.
- Confirm the VM remains isolated from customer data export paths.
PLAN

if [[ "${BLOCKED}" -gt 0 ]]; then
  info "offline update plan blocked: ${BLOCKED} blocked item(s), ${WARNINGS} warning(s)"
  exit 1
fi

if [[ "${WARNINGS}" -gt 0 ]]; then
  info "offline update plan completed with ${WARNINGS} warning(s); resolve or document them before updating"
else
  info "offline update plan ready"
fi
