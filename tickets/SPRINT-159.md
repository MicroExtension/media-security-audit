# Sprint 159 - Mission Export Manifest Downloads

## Goal

Let technicians download the mission export ZIP manifest without opening or
extracting the package.

## Scope

- Add JSON and Markdown manifest export builders.
- Read `manifest.json` from an existing mission package only.
- Add mission page links for manifest JSON and Markdown downloads.
- Add a guarded web download route for manifest exports.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No archive extraction workflow.
- No customer network activity.

## Acceptance Criteria

- Mission pages link to manifest JSON and Markdown downloads.
- Manifest exports include mission metadata, counts, checksums, and package members.
- Missing or invalid packages return clear errors.
- The workflow remains read-only and ZIP-manifest based.
