# Sprint 180 - Pilot Attention Markdown Export

## Goal

Export pilot attention items as Markdown for handoff follow-up.

## Scope

- Add a local Markdown export for non-ready pilot attention items.
- Add a `/pilot/attention.md` web route.
- Link the export from the Pilot page and Attention section.
- Keep existing Pilot exports unchanged.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for attention export generation.

## Acceptance Criteria

- The Pilot page links to the attention Markdown export.
- The export lists warning and blocked readiness items with review links.
- Empty attention input produces a clear no-open-item row.
- Existing Pilot bundle, manifest, verification, readiness, and runbook exports continue to work.
- Unit tests cover route wiring and export content.
