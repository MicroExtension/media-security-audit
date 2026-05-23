# Sprint 131 - Diagnostics Offline Package Inventory

## Goal

Include offline update package inventory in Debian VM diagnostics so support can
see package manifest status alongside bundle status.

## Scope

- Update `scripts/debian-vm-diagnostics.sh`.
- Add offline update package inventory with `--verify-manifests`.
- Keep diagnostics log-free, customer-data-free, extraction-free, and
  scanner-free.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Diagnostics reports include an `Offline Update Package Inventory` section.
- Offline package inventory failures are recorded in the diagnostics report.
- Diagnostics still finish when offline package inventory cannot complete.
- No package application, extraction, service startup beyond existing preflight
  behavior, log collection, scanner, or destructive operation is introduced.

## Safety

- No live scanner execution.
- No Docker service startup beyond existing preflight behavior.
- No archive extraction.
- No package application.
- No customer data collection.
- No destructive filesystem operations.
