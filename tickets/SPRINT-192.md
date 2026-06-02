# Sprint 192 - Pilot Sign-off JSON

## Goal

Group the Pilot sign-off automation work into one sprint by adding structured
JSON exports for the acceptance checklist and delivery receipt, then including
both files in the evidence bundle.

## Scope

- Add `/pilot/acceptance.json` for the beta acceptance checklist.
- Add `/pilot/delivery-receipt.json` for the delivery sign-off receipt.
- Link both JSON exports from the Pilot page actions, bundle area, and
  acceptance area.
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

- The Pilot page links to acceptance and delivery JSON downloads.
- The two JSON exports are deterministic and machine-readable.
- The Pilot ZIP includes both sign-off JSON files.
- The manifest hashes and file count account for both JSON files.
- Existing Pilot Markdown, readiness, manifest, verification, inventory, and
  bundle exports continue to work.
- Unit tests cover routes, template links, JSON payloads, and archived files.
