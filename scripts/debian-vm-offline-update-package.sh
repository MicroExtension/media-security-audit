#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

OUTPUT_DIR="${MEDIA_AUDIT_OFFLINE_UPDATE_DIR:-dist/offline-updates}"

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-offline-update-package.sh [--output-dir <path>]

Create a source-only offline update package from tracked Git files.

This helper does not apply updates, extract archives, build images, restart
services, collect logs, or include local customer data folders.
USAGE
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --output-dir)
      [[ "$#" -ge 2 ]] || fail "--output-dir requires a path"
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --output-dir=*)
      OUTPUT_DIR="${1#--output-dir=}"
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

command -v awk >/dev/null 2>&1 || fail "awk is required before running this script"
command -v basename >/dev/null 2>&1 || fail "basename is required before running this script"
command -v date >/dev/null 2>&1 || fail "date is required before running this script"
command -v git >/dev/null 2>&1 || fail "git is required before running this script"
command -v mkdir >/dev/null 2>&1 || fail "mkdir is required before running this script"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required before running this script"
command -v stat >/dev/null 2>&1 || fail "stat is required before running this script"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
CURRENT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

[[ "${CURRENT_BRANCH}" == "main" ]] || fail "switch to main before creating an offline update package"

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  fail "tracked local changes detected; commit or revert them before packaging"
fi

mkdir -p "${OUTPUT_DIR}"
[[ -w "${OUTPUT_DIR}" ]] || fail "${OUTPUT_DIR} is not writable by the current user"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PACKAGE_ROOT="media-security-audit-${CURRENT_COMMIT}"
PACKAGE="${OUTPUT_DIR}/media-audit-offline-update-${TIMESTAMP}-${CURRENT_COMMIT}.tgz"

info "creating source-only offline update package ${PACKAGE}"
git archive \
  --format=tar.gz \
  --prefix="${PACKAGE_ROOT}/" \
  --output="${PACKAGE}" \
  HEAD

PACKAGE_MANIFEST="${PACKAGE}.manifest.txt"
PACKAGE_NAME="$(basename "${PACKAGE}")"
PACKAGE_SIZE_BYTES="$(stat -c '%s' "${PACKAGE}")"
PACKAGE_SHA256="$(sha256sum "${PACKAGE}" | awk '{print $1}')"

info "writing offline update package manifest ${PACKAGE_MANIFEST}"
cat >"${PACKAGE_MANIFEST}" <<EOF
# MEDIA Security Audit Offline Update Package Manifest
generated_at_utc=${TIMESTAMP}
package=${PACKAGE_NAME}
source_branch=${CURRENT_BRANCH}
source_commit=${CURRENT_COMMIT}
size_bytes=${PACKAGE_SIZE_BYTES}
sha256=${PACKAGE_SHA256}
contents=git_tracked_source_only
excludes=data,runs,reports,evidence,.env,.git
application=not_implemented
EOF

info "offline update package ready: ${PACKAGE}"
info "offline update package manifest ready: ${PACKAGE_MANIFEST}"
info "review package and manifest before copying them to a customer VM."
