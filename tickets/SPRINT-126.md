# Sprint 126 - Offline Update Plan

## Goal

Give technicians a read-only planning helper for customer VMs that cannot use
internet-based updates during maintenance.

## Scope

- Add `scripts/debian-vm-offline-update-plan.sh`.
- Check branch, tracked changes, `.env`, authentication, and backup readiness.
- Accept an optional offline package and sidecar manifest.
- Verify package size and SHA-256 metadata when a manifest is available.
- Update README, deployment notes, next steps, roadmap, and owner intervention
  notes.
- Extend deployment file tests.

## Acceptance Criteria

- Offline update planning does not apply packages, extract archives, pull code,
  build images, restart services, collect logs, or run scanners.
- Package metadata checks are checksum-only and size-only.
- The helper can run before offline package application exists.
- Missing package metadata produces warnings or blocked items rather than hidden
  assumptions.

## Safety

- No live scanner execution.
- No Git pull.
- No Docker build, run, or service startup.
- No archive extraction.
- No customer data collection.
- No destructive filesystem operations.
