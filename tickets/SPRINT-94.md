# Sprint 94 - Preflight JSON Schema Summary

## Goal

Make deployment preflight JSON easier to consume from installation scripts and
future appliance automation.

## Scope

- Add a versioned JSON schema marker to preflight output.
- Add deterministic per-status summary counts.
- Keep the existing text output unchanged.
- Update tests and deployment documentation.

## Acceptance Criteria

- `media-audit preflight --format json` includes `schema_version`.
- JSON output includes summary counts for `ready`, `warning`, `missing`, and
  `blocked` checks.
- Existing text preflight output remains unchanged.
- No scanner command is executed.

## Safety

- This sprint only changes local preflight formatting helpers.
- No scanner execution is added.
- No network activity is added.
