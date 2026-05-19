# Sprint 104 - Debian VM Status Helper

## Goal

Give technicians a quick local status command for deployed VMs without
collecting logs, customer files, or running scanners.

## Scope

- Add `scripts/debian-vm-status.sh`.
- Report `.env` presence and web password configuration without printing the
  password.
- Report Docker Compose configuration status.
- Show `docker compose ps`.
- Show deployment preflight JSON.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper does not start, build, or update services.
- The helper does not collect Docker Compose logs.
- The helper does not run scanners.
- The helper does not print customer file contents.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper only reports local deployment status.
