# Sprint 98 - Debian VM Update Helper

## Goal

Give technicians a guarded update command for approved appliance changes on
customer VMs.

## Scope

- Add `scripts/debian-vm-update.sh`.
- Require Docker Compose, `.env`, web password, and the `main` branch.
- Refuse to update when tracked local changes are present.
- Run the local backup helper before pulling changes.
- Pull with `git pull --ff-only`.
- Build the image, run strict preflight, then restart Docker Compose.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- Updates are preceded by a local backup.
- Updates require a clean tracked worktree.
- The helper uses fast-forward-only Git updates.
- Docker Compose restart happens only after strict preflight.
- No scanner command is executed.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper only updates the code from Git, validates the VM, and restarts the
  local service after strict preflight passes.
