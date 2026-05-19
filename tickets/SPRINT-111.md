# Sprint 111 - Debian VM Handoff Report

## Goal

Give technicians a local handoff report before customer use, built from safe
readiness checks rather than logs or customer data.

## Scope

- Add `scripts/debian-vm-handoff-report.sh`.
- Write reports under `reports/handoff` by default.
- Allow `MEDIA_AUDIT_HANDOFF_DIR` to override the destination.
- Include the existing security review output.
- Include the existing deployment status output.
- Add technician review reminders.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper writes a timestamped handoff report.
- The helper exits non-zero when a safe readiness check fails.
- The helper does not print `.env` contents.
- The helper does not collect application logs.
- The helper does not start services, install packages, or run scanners.
- Documentation explains review before sharing.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The report is intended for local customer handoff review only.
