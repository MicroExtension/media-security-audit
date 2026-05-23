# Sprint 138 - Preview Inventory Reports

## Goal

Include offline update preview inventory status in maintenance and diagnostics
reports without applying or extracting any offline update package.

## Scope

- Extend `scripts/debian-vm-maintenance-report.sh`.
- Extend `scripts/debian-vm-diagnostics.sh`.
- Run `scripts/debian-vm-offline-update-preview-inventory.sh --verify-manifests`
  from both reports.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Maintenance reports include offline preview inventory status.
- Diagnostics include offline preview inventory status.
- Failed preview inventory verification marks maintenance as failed.
- Diagnostics record preview inventory status without failing support collection.
- The helpers do not extract packages, apply updates, start services, collect
  application logs, or run scanners.

## Safety

- No live scanner execution.
- No package application.
- No package extraction.
- No customer data collection.
- No application logs collected.
- No destructive filesystem operations.
