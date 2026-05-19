# Sprint 101 - Debian VM Diagnostics Helper

## Goal

Give technicians a safe support report for troubleshooting a deployed VM without
collecting customer data files or application logs.

## Scope

- Add `scripts/debian-vm-diagnostics.sh`.
- Capture Git branch, commit, and tracked status.
- Capture Docker Compose config status and service status.
- Capture persistent folder sizes without listing customer file names.
- Capture deployment preflight JSON.
- Write reports under `reports/support` by default.
- Update documentation and static safety tests.

## Acceptance Criteria

- Diagnostics do not include Docker Compose logs.
- Diagnostics do not archive or bundle customer folders.
- Diagnostics do not run scanners.
- Diagnostics include preflight JSON for automation-friendly support review.
- Support destination can be overridden with `MEDIA_AUDIT_SUPPORT_DIR`.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper collects coarse VM and deployment state only.
