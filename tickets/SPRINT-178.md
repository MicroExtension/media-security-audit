# Sprint 178 - Pilot Readiness Rollup

## Goal

Show a compact pilot readiness rollup before handoff.

## Scope

- Add a readiness rollup model with global status and ready, warning, blocked,
  and total counts.
- Show the rollup near the top of the Pilot page.
- Keep existing readiness Markdown, bundle, manifest, and verification exports
  unchanged.
- Keep rollup generation local and deterministic.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for rollup generation.

## Acceptance Criteria

- The Pilot page shows status, ready, warning, and blocked counters.
- Empty readiness input produces a warning rollup.
- Mixed readiness input produces expected counts and global status.
- Existing Pilot exports continue to work.
- Unit tests cover template wiring and rollup values.
