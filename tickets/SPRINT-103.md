# Sprint 103 - Debian VM Start Helper

## Goal

Make first startup safer by running strict deployment preflight before starting
the Docker Compose service.

## Scope

- Add `scripts/debian-vm-start.sh`.
- Require Docker Compose and a configured `.env`.
- Refuse startup when the web password is missing.
- Run `scripts/debian-vm-preflight.sh` before `docker compose up -d`.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- Startup runs strict preflight first.
- Docker Compose starts only after preflight helper succeeds.
- The helper does not install packages or call `sudo`.
- The helper does not run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper only validates local deployment readiness and starts the local
  service.
