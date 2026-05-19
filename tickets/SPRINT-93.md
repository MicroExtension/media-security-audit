# Sprint 93 - Preflight Strict Mode

## Goal

Allow install scripts and deployment gates to fail when preflight produces a
warning, while keeping the default technician workflow tolerant of warnings.

## Scope

- Add strict mode to deployment preflight exit-code handling.
- Expose `--strict` in the Typer CLI.
- Expose `--strict` in the argparse fallback CLI.
- Add tests for default and strict behavior.
- Update deployment notes.

## Acceptance Criteria

- Default preflight exits successfully on warning.
- `media-audit preflight --strict` exits non-zero on warning.
- Blocked status remains non-zero in all modes.
- Text and JSON output formats remain unchanged.
- No scanner command is executed.

## Safety

- This sprint only changes local preflight exit-code policy.
- No scanner execution is added.
- No network activity is added.
