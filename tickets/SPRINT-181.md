# Sprint 181 - Pilot Bundle Attention File

## Goal

Include the pilot attention Markdown export in the pilot evidence bundle.

## Scope

- Add `pilot-attention.md` to generated pilot evidence files.
- Ensure the ZIP, manifest, verification sheet, and visible inventory include
  the attention file automatically.
- Keep standalone attention, readiness, runbook, acceptance, manifest, and
  verification exports working.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for bundle generation.

## Acceptance Criteria

- The pilot ZIP contains `pilot-attention.md`.
- The standalone manifest lists `pilot-attention.md`.
- The verification sheet and Pilot page inventory include the attention file.
- Existing Pilot exports continue to work.
- Unit tests cover bundle content and manifest parity.
