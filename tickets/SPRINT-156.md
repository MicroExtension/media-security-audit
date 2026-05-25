# Sprint 156 - CLI Mission Export Verification

## Goal

Let technicians verify mission export ZIP packages from the CLI after generation
or handoff.

## Scope

- Add a `mission export-verify` CLI command.
- Support verification by mission id and reports directory.
- Support verification by explicit ZIP path.
- Support text and JSON output.
- Add a strict mode that fails on warning or failed integrity status.
- Document the read-only verification workflow.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No browser launch controls.
- No customer network activity.

## Acceptance Criteria

- The command reports status, detail, checked file count, and issue counts.
- JSON output is deterministic for automation.
- Missing or invalid packages return a non-zero exit code.
- Successful verification does not create scan run records.
