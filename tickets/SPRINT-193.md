# Sprint 193 - Pilot Review JSON

## Goal

Group the Pilot review automation work into one sprint by adding structured
JSON exports for the evidence bundle index and attention items, then including
both files in the evidence bundle.

## Scope

- Add `/pilot/bundle-index.json` for the evidence review order.
- Add `/pilot/attention.json` for remaining warnings and blockers.
- Link both JSON exports from the Pilot page actions and relevant sections.
- Include both JSON files in the Pilot evidence ZIP.
- Update manifest, inventory CSV, verification Markdown, and verification JSON
  output for the expanded bundle.
- Update README, roadmap, and next-step notes.

## Out of scope

- No live scan execution.
- No network activity.
- No customer data collection.
- No destructive validation.
- No disk writes for JSON or bundle generation.

## Acceptance Criteria

- The Pilot page links to bundle index and attention JSON downloads.
- The two JSON exports are deterministic and machine-readable.
- The Pilot ZIP includes both review JSON files.
- The manifest hashes and file count account for both JSON files.
- Existing Pilot Markdown, readiness, sign-off, manifest, verification,
  inventory, and bundle exports continue to work.
- Unit tests cover routes, template links, JSON payloads, and archived files.
