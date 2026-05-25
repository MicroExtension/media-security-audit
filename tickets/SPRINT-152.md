# Sprint 152 - Scan Plan Exports

## Goal

Make the consolidated scan plan easy to review and share before any guarded CLI
execution.

## Scope

- Move scan plan rendering into a shared read-only module.
- Keep CLI `scan plan-all` output aligned with the shared renderer.
- Add JSON and Markdown scan plan downloads from mission pages.
- Include both scan plan files in mission export ZIP packages.
- Add scan plan summary metadata to the mission export manifest.

## Out Of Scope

- No browser scan execution.
- No scanner execution changes.
- No live network activity.
- No customer evidence collection.

## Acceptance Criteria

- CLI scan plan tests still pass.
- Scan plan export tests cover JSON, text, and Markdown output.
- Mission ZIP exports include `scan-plan/*.json` and `scan-plan/*.md`.
- Mission export integrity verification covers the new scan plan files.
- Documentation explains that scan plan exports are read-only and not executed.
