# Sprint 6 - Local Web Authentication

## Goal

Add a first authentication guard for the local web interface before LAN
deployment becomes common.

## Scope

1. Add configurable HTTP Basic authentication for protected web routes.
2. Keep `/healthz` public for container health checks.
3. Require a non-placeholder password when auth is enabled.
4. Require a web password in Docker Compose before startup.
5. Document password setup and local development bypass.
6. Add unit tests for authentication settings and deployment defaults.

## Safety Constraints

- Docker deployments must require authentication by default.
- Placeholder passwords must be rejected by the app.
- Health checks must not expose mission data.
- Full user management is out of scope for this sprint.

## Acceptance Criteria

- Direct local development can run without auth unless explicitly enabled.
- Docker Compose requires `MEDIA_AUDIT_WEB_PASSWORD`.
- Protected routes use HTTP Basic when auth is enabled.
- Auth tests cover missing, placeholder, invalid, and valid credentials.
