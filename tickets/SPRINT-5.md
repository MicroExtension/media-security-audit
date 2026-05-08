# Sprint 5 - Docker Deployment Foundation

## Goal

Prepare a reproducible local deployment path for Debian/Ubuntu customer VMs.

## Scope

1. Add a Dockerfile for the local web UI.
2. Add Docker Compose with persistent local folders.
3. Add `.env.example` for bind address and port.
4. Document first install, updates, backups, and CLI usage in Docker.
5. Add tests that validate deployment guardrails without running Docker.

## Safety Constraints

- Default host bind must be `127.0.0.1`.
- LAN exposure must require an explicit `.env` change.
- Persistent audit data must stay outside the image.
- The container must run as a non-root user.
- Scanner execution remains guarded by the application.

## Acceptance Criteria

- `docker compose up -d --build` can start the local web service.
- `data`, `runs`, `reports`, and `evidence` are persisted as host folders.
- Deployment docs explain local-only and LAN access modes.
- Tests assert core deployment defaults and persistence paths.
