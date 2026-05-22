# Sprint 125 - Support Bundle Inventory

## Goal

Include shareable bundle inventory in Debian VM diagnostics so support review can
see bundle manifest status without asking a technician to run a second command.

## Scope

- Update `scripts/debian-vm-diagnostics.sh`.
- Add bundle inventory with `--verify-manifests`.
- Keep diagnostics log-free, customer-data-free, and scanner-free.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Diagnostics reports include a `Bundle Inventory` section.
- Bundle inventory failures are recorded in the diagnostics report.
- Diagnostics still finish when bundle inventory cannot complete.
- No service startup beyond existing status/preflight behavior, log collection,
  extraction, restore, scanner, or destructive operation is introduced.

## Safety

- No live scanner execution.
- No Docker service startup beyond existing preflight behavior.
- No customer data collection.
- No destructive filesystem operations.
