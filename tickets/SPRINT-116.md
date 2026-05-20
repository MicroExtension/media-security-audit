# Sprint 116 - Update Backup Manifest Gate

## Goal

Make approved Debian VM updates rely on a freshly manifested and verified
backup before the helper pulls code or restarts services.

## Scope

- Update `scripts/debian-vm-update.sh` to create, manifest, and verify the
  latest local backup before `git pull --ff-only`.
- Update `scripts/debian-vm-update-plan.sh` to surface latest-backup manifest
  readiness without applying changes.
- Update README, roadmap, deployment notes, and owner next steps.
- Extend deployment file tests for the new update guardrail.

## Acceptance Criteria

- The update helper fails if a new local backup cannot be found.
- The update helper runs the backup manifest helper and manifest verification
  helper before pulling code.
- The update plan remains read-only and warns when the latest backup is missing
  a sidecar manifest.
- No scanner, log collection, or destructive operation is introduced.

## Safety

- No live scanner execution.
- No Docker service startup during development.
- No customer data collection.
- No destructive filesystem operations.
