# Sprint 175 - Pilot Evidence Manifest Export

## Goal

Expose the pilot evidence bundle manifest as a standalone JSON download before
handoff.

## Scope

- Reuse the same manifest payload for the ZIP bundle and public JSON export.
- Add a `/pilot/bundle-manifest.json` web route.
- Link the manifest from the Pilot page.
- Keep manifest generation local, deterministic, and in memory.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for manifest generation.

## Acceptance Criteria

- The Pilot page links to the standalone manifest JSON.
- The ZIP `manifest.json` matches the standalone manifest payload.
- Manifest entries continue to include path, byte size, and SHA-256 checksum.
- Existing bundle and Markdown exports continue to work.
- Unit tests cover route wiring and manifest parity.
