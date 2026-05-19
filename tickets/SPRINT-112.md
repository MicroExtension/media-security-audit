# Sprint 112 - Debian VM Update Plan

## Goal

Give technicians a read-only update readiness check before an approved
maintenance window.

## Scope

- Add `scripts/debian-vm-update-plan.sh`.
- Check that the VM clone is on `main`.
- Check for tracked local changes.
- Check `.env`, Web password, and authentication settings.
- Check for a local backup archive candidate.
- Print the reviewed backup and update commands without executing them.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper exits non-zero when blocked checks are present.
- The helper warns when no local backup archive is found.
- The helper does not pull code.
- The helper does not build or restart Docker services.
- The helper does not collect application logs.
- The helper does not install packages or run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper is planning-only; `scripts/debian-vm-update.sh` remains the
  explicit maintenance action.
