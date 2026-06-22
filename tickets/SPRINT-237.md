# Sprint 237 - Pilot Real Condition Exports

## Goal

Make the real-condition trial checklist easy to download and archive as its own
handoff artifact.

## Scope

- Add Markdown and JSON exports for the Pilot real-condition trial checklist.
- Link both exports from the Pilot page.
- Include both files in the Pilot evidence bundle, manifest, index, inventory,
  handoff summary, delivery receipt, and verification outputs.
- Update schema versions where the file inventory changes.
- Update tests and product notes.

## Acceptance Criteria

- `/pilot/real-condition.md` downloads the human checklist.
- `/pilot/real-condition.json` downloads the machine-readable checklist.
- The Pilot evidence bundle includes both files.
- Manifest, inventory, verification, handoff, and delivery outputs account for
  the new files.
- Tests cover the new routes, exports, bundle files, and schema counts.

## Safety

- No scanner execution added.
- No network activity added.
- No authorization bypass added.
