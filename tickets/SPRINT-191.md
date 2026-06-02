# Sprint 191 - Pilot Bundle Handoff JSON

## Goal

Include the Pilot handoff JSON summary in the evidence bundle so automation can
consume handoff state from the same ZIP already used for technician evidence.

## Scope

- Add `pilot-handoff-summary.json` to the Pilot evidence bundle.
- Include the JSON file in the manifest, verification outputs, inventory, and
  recommended review order.
- Mention the JSON handoff file in handoff summary, bundle index, and delivery
  receipt content.
- Update README, roadmap, and next-step notes.

## Out of scope

- No live scan execution.
- No network activity.
- No customer data collection.
- No manifest schema structure change.
- No disk writes for bundle generation.

## Acceptance Criteria

- The Pilot ZIP includes `pilot-handoff-summary.json`.
- The manifest hashes and file count account for the JSON handoff file.
- Verification Markdown and JSON include the updated review order and file count.
- Existing Pilot standalone downloads continue to work.
- Unit tests cover bundle contents, manifest entries, and archived JSON content.
