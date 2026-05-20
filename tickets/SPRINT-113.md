# Sprint 113 - Debian VM Handoff Bundle

## Goal

Give technicians a shareable handoff archive that contains only the local VM
handoff report.

## Scope

- Add `scripts/debian-vm-handoff-bundle.sh`.
- Generate a fresh handoff report with the existing handoff helper.
- Archive only the generated handoff text report.
- Allow `MEDIA_AUDIT_HANDOFF_BUNDLE_DIR` to override the bundle destination.
- Preserve the handoff report exit status after the bundle is written.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper creates a `.tgz` handoff bundle.
- The bundle is based on a fresh handoff report.
- The bundle archive uses the handoff directory as its archive root.
- The helper does not archive `data`, `runs`, `reports`, or `evidence`.
- The helper does not collect application logs.
- The helper does not start services, install packages, or run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The generated bundle must be reviewed before it is shared.
