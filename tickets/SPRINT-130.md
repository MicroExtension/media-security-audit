# Sprint 130 - Maintenance Offline Package Inventory

## Goal

Include offline update package inventory in Debian VM maintenance reports so a
technician can review package manifest status during pre-maintenance checks.

## Scope

- Update `scripts/debian-vm-maintenance-report.sh`.
- Add offline update package inventory with `--verify-manifests`.
- Keep the report log-free, customer-data-free, restore-free, and scanner-free.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Maintenance reports include an `Offline Update Package Inventory` section.
- Offline package inventory failures make the maintenance report exit non-zero.
- Technician review reminds operators to verify offline package manifests before
  offline maintenance.
- No package application, extraction, service startup, log collection, scanner,
  or destructive operation is introduced.

## Safety

- No live scanner execution.
- No Docker service startup.
- No archive extraction.
- No package application.
- No customer data collection.
- No destructive filesystem operations.
