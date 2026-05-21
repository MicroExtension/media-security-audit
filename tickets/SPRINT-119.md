# Sprint 119 - Debian VM Maintenance Bundle

## Goal

Add a shareable pre-maintenance bundle that contains only the generated
maintenance report.

## Scope

- Add `scripts/debian-vm-maintenance-bundle.sh`.
- Generate a fresh maintenance report before packaging.
- Package only the latest `media-audit-maintenance-*.txt` report.
- Document the helper in README, deployment notes, next steps, and roadmap.
- Extend deployment file tests for bundle safety.

## Acceptance Criteria

- The helper writes a timestamped `.tgz` bundle.
- The bundle command exits with the maintenance report status.
- The archive includes only the maintenance report, not repository root,
  persistent folders, customer data, or application logs.
- No scanner, Docker service startup, extraction, restore, or destructive
  operation is introduced.

## Safety

- No live scanner execution.
- No Docker service startup.
- No customer data collection.
- No destructive filesystem operations.
