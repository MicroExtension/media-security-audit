# Sprint 135 - Offline Plan Preview Check

## Goal

Connect offline update planning to verified preview folders without applying any
offline update package.

## Scope

- Extend `scripts/debian-vm-offline-update-plan.sh` with `--preview`.
- Verify the preview manifest during planning when a preview folder is provided.
- Keep preview verification read-only and package-metadata focused.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Offline planning can check package metadata and preview metadata together.
- Offline planning reports a blocked item when preview verification fails.
- Offline planning still does not extract packages, apply updates, pull code,
  build images, restart services, collect logs, or run scanners.
- Offline package application remains unimplemented.

## Safety

- No live scanner execution.
- No Git pull.
- No Docker build, run, or service startup.
- No package extraction by the plan helper.
- No package application.
- No customer data collection.
- No destructive filesystem operations.
