# Sprint 107 - Debian VM Support Bundle

## Goal

Give technicians a simple support archive for VM troubleshooting without
including customer folders or application logs.

## Scope

- Add `scripts/debian-vm-support-bundle.sh`.
- Generate a fresh diagnostics report with the existing diagnostics helper.
- Archive only the generated diagnostics text report.
- Allow `MEDIA_AUDIT_SUPPORT_BUNDLE_DIR` to override the bundle destination.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper creates a `.tgz` support bundle.
- The bundle is based on a fresh diagnostics report.
- The bundle archive uses the support directory as its archive root.
- The helper does not archive `data`, `runs`, `reports`, or `evidence`.
- The helper does not collect application logs.
- The helper does not start services, install packages, or run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The generated bundle must be reviewed before it is shared.
