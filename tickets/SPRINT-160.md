# Sprint 160 - CLI Mission Export Manifest

## Goal

Let technicians print a mission export ZIP manifest from the CLI after package
generation or handoff.

## Scope

- Add a `mission export-manifest` CLI command.
- Support lookup by mission id and reports directory.
- Support lookup by explicit ZIP package path.
- Support JSON and Markdown output.
- Reuse the same manifest formatter used by web downloads.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No archive extraction workflow.
- No customer network activity.

## Acceptance Criteria

- JSON output contains the ZIP manifest object.
- Markdown output includes mission metadata, counts, checksums, and package members.
- The command reads only `manifest.json` from an existing ZIP.
- Running the command does not create scan run records.
