# Sprint 174 - Pilot Evidence Bundle

## Goal

Package the local pilot handoff evidence into a single ZIP download from the
Pilot page.

## Scope

- Add a local pilot evidence bundle generator.
- Include the pilot runbook, acceptance checklist, readiness summary, and a
  JSON manifest with checksums.
- Expose the bundle from the local web UI.
- Keep bundle generation in memory and deterministic.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for bundle generation.

## Acceptance Criteria

- The Pilot page links to a ZIP evidence bundle.
- The ZIP contains only Markdown pilot evidence and a manifest.
- Manifest entries include path, byte size, and SHA-256 checksum.
- Existing Markdown exports continue to work.
- Unit tests cover bundle content and web route wiring.
