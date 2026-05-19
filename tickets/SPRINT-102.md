# Sprint 102 - Debian VM Environment Initialization Helper

## Goal

Make first install safer and faster by generating a local-only authenticated
`.env` file for Debian/Ubuntu VM deployments.

## Scope

- Add `scripts/debian-vm-init-env.sh`.
- Refuse to overwrite an existing `.env`.
- Generate a strong web password with Python `secrets`.
- Default to `MEDIA_AUDIT_BIND=127.0.0.1`.
- Enable web authentication by default.
- Restrict `.env` file permissions.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper creates a `.env` with authentication enabled.
- The helper does not bind the UI to LAN by default.
- The helper refuses to overwrite existing configuration.
- The helper does not install packages or call `sudo`.
- The helper does not run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted.
- The helper only writes first-install local configuration.
