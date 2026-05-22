# Sprint 123 - Maintenance Bundle Inventory

## Goal

Include shareable bundle inventory in the Debian VM maintenance report so
technicians can review backup and bundle manifest status in one file.

## Scope

- Update `scripts/debian-vm-maintenance-report.sh`.
- Add bundle inventory with `--verify-manifests`.
- Keep the report log-free, restore-free, and scanner-free.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Maintenance reports include a `Bundle Inventory` section.
- Bundle inventory failures make the maintenance report exit non-zero.
- Technician review reminds operators to verify shareable bundle manifests.
- No service startup, log collection, extraction, restore, scanner, or
  destructive operation is introduced.

## Safety

- No live scanner execution.
- No Docker service startup.
- No customer data collection.
- No destructive filesystem operations.
