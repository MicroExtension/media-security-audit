#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

CONFIRM=false
INIT_ENV=false
CURRENT_USER="${SUDO_USER:-${USER:-${USERNAME:-}}}"

usage() {
  cat <<'USAGE'
Usage: bash scripts/debian-vm-bootstrap.sh [--confirm] [--init-env]

Prepares a fresh Debian/Ubuntu VM for the MEDIA Security Audit local appliance.
Default mode is a plan only: it prints checks and reviewed commands without
installing packages, changing groups, starting services, creating .env, running
Docker, running scanners, or updating scanner templates.

Options:
  --confirm   Execute the approved system preparation commands.
  --init-env  After confirmed bootstrap, create .env with local-only authenticated
              defaults if .env does not already exist.
  --help      Show this help.
USAGE
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

info() {
  printf '[media-audit] %s\n' "$1"
}

status() {
  local label="$1"
  local detail="$2"
  printf '[media-audit] %-22s %s\n' "${label}" "${detail}"
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

has_compose_v2() {
  has_command docker && docker compose version >/dev/null 2>&1
}

apt_package_available() {
  apt-cache show "$1" >/dev/null 2>&1
}

install_compose_provider_if_needed() {
  if has_compose_v2; then
    info "Docker Compose v2 is already available"
    return
  fi

  info "Docker Compose v2 not found after docker.io installation; checking distribution packages"
  if apt_package_available docker-compose-plugin; then
    sudo apt install -y docker-compose-plugin
  elif apt_package_available docker-compose-v2; then
    sudo apt install -y docker-compose-v2
  else
    fail "Docker Compose v2 is missing; install the distribution package that provides 'docker compose' and rerun this helper"
  fi

  has_compose_v2 || fail "Docker Compose v2 is still unavailable after package installation"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --confirm)
      CONFIRM=true
      shift
      ;;
    --init-env)
      INIT_ENV=true
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      usage
      fail "unknown argument: $1"
      ;;
  esac
done

info "VM bootstrap helper for Debian/Ubuntu local appliance deployment"

[[ -n "${CURRENT_USER}" ]] || fail "unable to detect the technician user; run this helper from a normal login shell"

if has_command git; then
  status "git" "ready at $(command -v git)"
else
  status "git" "missing; installed by --confirm"
fi

if has_command docker; then
  status "docker" "ready at $(command -v docker)"
else
  status "docker" "missing; installed by --confirm"
fi

if has_compose_v2; then
  status "docker compose" "ready"
else
  status "docker compose" "missing; package name varies by distribution"
fi

if [[ -f ".env" ]]; then
  status ".env" "present; not overwritten"
else
  status ".env" "missing; use --init-env with --confirm to create local-only auth defaults"
fi

if [[ "${CONFIRM}" != "true" ]]; then
  info "bootstrap plan only; no package, group, service, Docker, scanner, or template command is executed"
  cat <<'PLAN'
Reviewed commands when --confirm is used:
  sudo apt update
  sudo apt install -y git docker.io
  sudo systemctl enable --now docker
  sudo apt install -y docker-compose-plugin
  sudo apt install -y docker-compose-v2
  sudo usermod -aG docker "$USER"

Only one Docker Compose provider is installed, and only if the package exists.
The helper checks both docker-compose-plugin and docker-compose-v2 because
package names vary between Debian and Ubuntu releases.

After confirmed bootstrap:
  log out and log back in if your user was added to the docker group
  bash scripts/debian-vm-init-env.sh
  bash scripts/debian-vm-security-review.sh
  bash scripts/debian-vm-preflight.sh
PLAN
  exit 0
fi

has_command sudo || fail "sudo is required for confirmed VM bootstrap"
has_command apt || fail "apt is required on Debian/Ubuntu VM bootstrap"
has_command apt-cache || fail "apt-cache is required to detect Docker Compose package availability"

info "installing core VM packages"
sudo apt update
sudo apt install -y git docker.io

info "enabling Docker service"
sudo systemctl enable --now docker

install_compose_provider_if_needed

if id -nG "${CURRENT_USER}" | grep -qw docker; then
  info "current user is already in the docker group"
else
  info "adding current user to the docker group; log out and back in before running docker without sudo"
  sudo usermod -aG docker "${CURRENT_USER}"
fi

if [[ "${INIT_ENV}" == "true" ]]; then
  if [[ -f ".env" ]]; then
    info ".env already exists; leaving it unchanged"
  else
    info "creating local-only authenticated .env"
    bash scripts/debian-vm-init-env.sh
  fi
fi

info "bootstrap complete"
info "next: log out and back in if group membership changed, then run bash scripts/debian-vm-security-review.sh"
