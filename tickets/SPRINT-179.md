# Sprint 179 - Pilot Attention Items

## Goal

Highlight pilot readiness warnings and blockers before handoff.

## Scope

- Add attention items derived from non-ready pilot readiness checks.
- Show a conditional Attention section on the Pilot page.
- Link each attention item back to its review target.
- Keep existing Pilot exports unchanged.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for attention item generation.

## Acceptance Criteria

- The Pilot page shows an Attention section when readiness has warning or blocked items.
- The Attention section links back to the relevant review targets.
- Empty or fully ready readiness input keeps the attention list empty.
- Existing Pilot bundle, manifest, verification, and Markdown exports continue to work.
- Unit tests cover template wiring and warning attention content.
