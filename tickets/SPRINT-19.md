# Sprint 19 - Run Monitor Foundation

## Goal

Record scan executions launched from the guarded CLI and display that history
inside the mission page without adding browser scan execution.

## Scope

1. Add a `ScanRun` domain model.
2. Store scan run records in local JSON files per mission.
3. Record completed and failed CLI runs for Nmap, HTTP headers, and DNS/Mail.
4. Show a Run Monitor section on mission pages.
5. Add tests for storage, CLI recording, and mission view output.

## Safety Constraints

- No scan execution route in the web application.
- No browser button starts a scanner.
- Existing CLI execution still requires `--execute`.
- Failed run recording must not hide the original execution error.
- Run records are local metadata only.

## Acceptance Criteria

- Successful CLI scan runs create local run records.
- Failed CLI scan runs create failed run records where execution has started.
- Mission pages list run status, check type, finding count, evidence count, and error.
- Unit tests cover run storage and Web view output.
