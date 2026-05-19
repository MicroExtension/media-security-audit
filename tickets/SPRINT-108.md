# Sprint 108 - Debian VM Password Rotation

## Goal

Give technicians a guarded way to rotate the local Web UI password on customer
VMs without disabling authentication or restarting services automatically.

## Scope

- Add `scripts/debian-vm-rotate-password.sh`.
- Require explicit `--confirm`.
- Generate a strong replacement `MEDIA_AUDIT_WEB_PASSWORD`.
- Force `MEDIA_AUDIT_REQUIRE_AUTH=true`.
- Back up the previous `.env` file before writing.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper refuses to run without `--confirm`.
- The helper requires an existing writable `.env`.
- The helper creates a timestamped `.env` backup.
- The helper keeps authentication enabled.
- The helper does not print the generated password to stdout.
- The helper does not restart Docker services automatically.
- The helper does not install packages or run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The generated password must be stored in the maintenance password vault before
  customer use continues.
