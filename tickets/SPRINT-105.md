# Sprint 105 - Debian VM Stop Helper

## Goal

Give technicians a guarded way to stop the local appliance service without
removing data.

## Scope

- Add `scripts/debian-vm-stop.sh`.
- Require explicit `--confirm`.
- Use `docker compose stop media-audit`.
- Avoid `down`, container removal, volume removal, and filesystem deletion.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper refuses to run without `--confirm`.
- The helper stops the service without deleting persistent folders.
- The helper does not call `docker compose down`, `docker compose rm`, or volume
  removal.
- The helper does not install packages or call `sudo`.
- The helper does not run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper only stops the local service and prints Compose status.
