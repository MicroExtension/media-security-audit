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

command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v find >/dev/null 2>&1 || fail "find is required before running this script"
command -v git >/dev/null 2>&1 || fail "git is required before running this script"
command -v grep >/dev/null 2>&1 || fail "grep is required before running this script"
command -v sort >/dev/null 2>&1 || fail "sort is required before running this script"
command -v tail >/dev/null 2>&1 || fail "tail is required before running this script"

info "planning update only; no update command is executed"
printf 'generated_at_utc=%s\n' "$(date -u +%Y%m%dT%H%M%SZ)"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
CURRENT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
printf 'current_branch=%s\n' "${CURRENT_BRANCH}"
printf 'current_commit=%s\n' "${CURRENT_COMMIT}"

if [[ "${CURRENT_BRANCH}" == "main" ]]; then
  record ready "Git branch" "VM clone is on main"
else
  record blocked "Git branch" "switch to main before updating this VM"
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
  else
    record warning "Local backup" "no local backup archive found in ${BACKUP_DIR}"
  fi
else
  record warning "Local backup" "${BACKUP_DIR} does not exist yet"
fi

printf '\n'
cat <<'PLAN'
Next reviewed commands, not executed by this helper:
  bash scripts/debian-vm-backup.sh
  bash scripts/debian-vm-update.sh

Review before update:
- Confirm a maintenance window is approved.
- Confirm the previous backup was verified when required.
- Confirm the VM has update internet access or use the future offline package process.
PLAN

if [[ "${BLOCKED}" -gt 0 ]]; then
  info "update plan blocked: ${BLOCKED} blocked item(s), ${WARNINGS} warning(s)"
  exit 1
fi

if [[ "${WARNINGS}" -gt 0 ]]; then
  info "update plan completed with ${WARNINGS} warning(s); resolve or document them before updating"
else
  info "update plan ready"
fi
