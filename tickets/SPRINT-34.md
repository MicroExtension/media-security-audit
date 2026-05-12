# Sprint 34 - Mission Export Integrity Verification

Goal: Verify mission export ZIP packages against their manifest before showing
the package as ready in the web interface.

## Scope

1. Read `manifest.json` from an existing mission export ZIP.
2. Validate every manifest `archive_files` entry against ZIP member presence,
   byte size, and SHA-256 hash.
3. Report `ready`, `warning`, or `failed` integrity status for the mission page.
4. Keep package generation and download behavior unchanged.
5. Add tests for valid and invalid package verification.

## Safety

- No scanner execution.
- No network activity.
- No change to mission data, findings, or report contents.
- Verification reads only generated package files.

## Acceptance Criteria

- A generated mission export package reports `ready`.
- Missing manifest members report `failed`.
- The mission page displays the package integrity status and detail.
- Tests cover both successful verification and a failed integrity check.
