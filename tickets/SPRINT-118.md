# Sprint 118 - Debian VM Maintenance Report

## Goal

Add a safe pre-maintenance report that aggregates local readiness checks before
approved customer-impacting work.

## Scope

- Add `scripts/debian-vm-maintenance-report.sh`.
- Include security review, backup inventory with manifest verification, and
  update plan output.
- Store reports under `reports/maintenance` by default.
- Document the helper in README, deployment notes, next steps, and roadmap.
- Extend deployment file tests for safety guardrails.

## Acceptance Criteria

- The helper writes a timestamped maintenance report.
- The helper exits non-zero if security review, backup inventory, or update
  planning reports a blocked condition.
- The helper does not start services, collect logs, extract backups, restore
  data, or run scanners.

## Safety

- No live scanner execution.
- No Docker service startup.
- No customer data collection.
- No destructive filesystem operations.
