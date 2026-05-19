# Sprint 106 - Debian VM Restart Helper

## Goal

Give technicians a guarded restart command for approved local appliance
maintenance without removing persistent data.

## Scope

- Add `scripts/debian-vm-restart.sh`.
- Require explicit `--confirm`.
- Reuse `scripts/debian-vm-stop.sh --confirm`.
- Reuse `scripts/debian-vm-start.sh` so strict preflight stays mandatory.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper refuses to run without `--confirm`.
- The helper stops before starting.
- The helper does not call `docker compose down`, `docker compose rm`, or volume
  removal.
- Startup still goes through strict deployment preflight.
- The helper does not install packages or call `sudo`.
- The helper does not run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper only chains the existing guarded stop and start operations.
