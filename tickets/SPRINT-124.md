# Sprint 124 - Handoff Bundle Inventory

## Goal

Include shareable bundle inventory in the Debian VM handoff report so customer
handoff review includes generated bundle manifest status.

## Scope

- Update `scripts/debian-vm-handoff-report.sh`.
- Add bundle inventory with `--verify-manifests`.
- Keep the report log-free, customer-data-free, and scanner-free.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Handoff reports include a `Bundle Inventory` section.
- Bundle inventory failures make the handoff report exit non-zero.
- Technician review reminds operators to verify shareable bundle manifests.
- No service startup beyond existing status checks, log collection, extraction,
  restore, scanner, or destructive operation is introduced.

## Safety

- No live scanner execution.
- No Docker service startup beyond existing status helper behavior.
- No customer data collection.
- No destructive filesystem operations.
