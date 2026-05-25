# Sprint 158 - Mission Export Verification Downloads

## Goal

Let technicians download the mission export verification result from the mission
page as a handoff artifact.

## Scope

- Add JSON and Markdown export builders for mission ZIP verification.
- Reuse the existing manifest-based verifier for Web and CLI output.
- Add mission page links for verification JSON and Markdown downloads.
- Add a guarded web download route for verification exports.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No customer network activity.

## Acceptance Criteria

- Mission pages link to ZIP verification JSON and Markdown downloads.
- Verification exports include status, detail, counts, and issue lists.
- CLI verification keeps producing deterministic JSON/text from the shared formatter.
- Missing mission packages still return a clear not-found error.
