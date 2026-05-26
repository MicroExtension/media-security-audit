# Sprint 161 - CLI Mission Export Inventory

## Goal

Let technicians list mission export ZIP packages and integrity status from the
CLI without opening the web interface.

## Scope

- Add mission export inventory builders.
- Add a `mission export-inventory` CLI command.
- Support text and JSON output.
- Support `--include-missing` to show missions without export packages.
- Include package path, size, status, detail, and integrity counters.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No archive extraction workflow.
- No customer network activity.

## Acceptance Criteria

- Existing packages are listed with integrity status.
- Missing packages can be included on request.
- JSON output has summary counts and item details.
- Running the command does not create scan run records.
