# Sprint 92 - Preflight JSON Output

## Goal

Make deployment preflight results usable by install scripts and monitoring
wrappers while preserving the technician-friendly text output.

## Scope

- Add a structured JSON formatter for deployment preflight results.
- Add `--format text|json` to the Typer and fallback CLI paths.
- Keep text output as the default.
- Add tests for JSON formatting and CLI output.
- Update deployment notes.

## Acceptance Criteria

- `media-audit preflight --format json` returns valid JSON.
- JSON output includes overall status and per-item category, label, status, and
  detail.
- Existing text output remains the default.
- Exit code behavior remains unchanged.
- No scanner command is executed.

## Safety

- This sprint only changes local preflight reporting.
- No scanner execution is added.
- No network activity is added.
