# Sprint 187 - Pilot Manifest Review Order

## Goal

Add a machine-readable review order to the pilot evidence manifest so extracted
bundle files can be reviewed consistently without relying on ZIP or filesystem
ordering.

## Scope

- Add a `review_order` field to the pilot evidence manifest.
- Bump the pilot evidence manifest schema version.
- Show the review order in the pilot evidence verification Markdown.
- Keep existing Pilot exports and bundle files unchanged.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for manifest or verification generation.

## Acceptance Criteria

- The pilot manifest exposes the recommended review order.
- The pilot verification Markdown shows the review order.
- Existing Pilot Markdown, JSON, manifest, and bundle exports continue to work.
- Unit tests cover schema version, review order content, and verification output.
