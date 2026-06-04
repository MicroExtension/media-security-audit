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

command -v docker >/dev/null 2>&1 || fail "docker is required before running this script"
command -v find >/dev/null 2>&1 || fail "find is required before running this script"
command -v git >/dev/null 2>&1 || fail "git is required before running this script"
command -v sort >/dev/null 2>&1 || fail "sort is required before running this script"
command -v tail >/dev/null 2>&1 || fail "tail is required before running this script"
docker compose version >/dev/null 2>&1 || fail "docker compose v2 is required before running this script"

[[ -f ".env" ]] || fail "copy .env.example to .env and set MEDIA_AUDIT_WEB_PASSWORD first"
grep -Eq '^MEDIA_AUDIT_WEB_PASSWORD=.+$' ".env" \
  || fail "set MEDIA_AUDIT_WEB_PASSWORD in .env before running this script"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[[ "${CURRENT_BRANCH}" == "main" ]] || fail "switch to main before updating this VM"

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  fail "tracked local changes detected; commit or revert them before updating"
fi

BACKUP_DIR="${MEDIA_AUDIT_BACKUP_DIR:-reports/backups}"

info "creating local backup before update"
bash scripts/debian-vm-backup.sh

LATEST_BACKUP="$(
  find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'media-audit-backup-*.tgz' -print \
    | sort \
    | tail -n 1
)"
[[ -n "${LATEST_BACKUP}" ]] || fail "local backup was not found after backup helper completed"

info "writing backup manifest before update"
bash scripts/debian-vm-backup-manifest.sh "${LATEST_BACKUP}"

info "verifying backup manifest before update"
bash scripts/debian-vm-verify-backup-manifest.sh "${LATEST_BACKUP}"

info "pulling latest approved main branch"
git pull --ff-only

info "validating Docker Compose configuration"
docker compose config --quiet

info "building updated media-audit image"
docker compose build media-audit

info "running strict deployment preflight"
docker compose run --rm media-audit media-audit preflight \
  --data-dir /var/lib/media-audit/data \
  --reports-dir /var/lib/media-audit/reports \
  --strict

info "starting updated service"
docker compose up -d

info "service status"
docker compose ps
