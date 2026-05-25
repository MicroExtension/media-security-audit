# Sprint 155 - Mission Readiness Exports

## Goal

Make mission readiness easy to share from the web UI and preserve it in mission
handoff packages.

## Scope

- Add JSON and Markdown readiness export builders.
- Add mission page readiness download links.
- Add a guarded web download route for readiness exports.
- Include readiness exports in mission ZIP packages.
- Add readiness summary metadata to mission export manifests.

## Out Of Scope

- No scanner execution.
- No browser scan launch controls.
- No customer network activity.
- No change to readiness rules.

## Acceptance Criteria

- Readiness JSON and Markdown exports are deterministic.
- Mission pages link to readiness exports.
- Mission ZIP packages include `readiness/*.json` and `readiness/*.md`.
- Mission export integrity verification covers readiness files.
- Tests prove readiness exports do not create scan run records.
