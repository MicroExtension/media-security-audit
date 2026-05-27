# Sprint 172 - Pilot Readiness Summary

## Goal

Make the Pilot page useful before a beta deployment by showing a read-only
summary of workspace readiness.

## Scope

- Add Pilot readiness view items.
- Summarize authentication, storage, clients, missions, mission exports,
  workspace backup, and external tool availability.
- Show the readiness section on `/pilot`.
- Link readiness items back to System, Dashboard, and Exports.
- Update documentation and regression tests.

## Out Of Scope

- No scanner execution changes.
- No live network activity.
- No data mutation workflow.
- No customer data export changes.

## Acceptance Criteria

- `/pilot` shows a Readiness section when local readiness items are provided.
- Readiness items are derived from existing local workspace/system data.
- Each readiness item has a status, detail, and review link.
- Tests cover the readiness builder, route wiring, and template wiring.
