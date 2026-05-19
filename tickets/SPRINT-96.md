# Sprint 96 - Debian VM Preflight Helper

## Goal

Give technicians a safe one-command check before starting the local appliance
on a Debian or Ubuntu customer VM.

## Scope

- Add a guarded `scripts/debian-vm-preflight.sh` helper.
- Check Docker Compose availability and `.env` password configuration.
- Create persistent local folders when missing.
- Validate Compose configuration, build the image, and run strict preflight.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper does not install packages or call `sudo`.
- The helper does not run scanners.
- The helper refuses to continue when `.env` or `MEDIA_AUDIT_WEB_PASSWORD` is
  missing.
- The helper runs `media-audit preflight --strict` through Docker Compose.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper only prepares local folders and runs deployment checks.
