# Sprint 176 - Pilot Bundle Verification Export

## Goal

Provide a human-readable Markdown verification sheet for the pilot evidence
bundle.

## Scope

- Build verification Markdown from the same manifest payload used by the ZIP
  and standalone JSON export.
- Add a `/pilot/bundle-verification.md` web route.
- Link the verification sheet from the Pilot page.
- Keep verification generation local, deterministic, and in memory.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for verification generation.

## Acceptance Criteria

- The Pilot page links to the verification Markdown export.
- The verification sheet lists file names, byte sizes, and SHA-256 values.
- The verification sheet includes technician handoff check steps.
- Existing bundle, manifest, and Markdown exports continue to work.
- Unit tests cover route wiring and verification content.
