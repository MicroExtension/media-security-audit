# Sprint 153 - Authorization Brief Scan Plan

## Goal

Make the customer authorization brief show the selected scan plan before any
guarded CLI execution is considered.

## Scope

- Add a scan plan section to Markdown authorization briefs.
- Add a scan plan section to HTML authorization briefs.
- Show ready and blocked check counts.
- Show planned command previews.
- Keep the explicit `not_executed` marker in the brief.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No browser scan launch controls.
- No customer network activity.
- No change to approval rules.

## Acceptance Criteria

- Authorization briefs include planned scan commands.
- Draft missions still show blocked scan plans.
- Generated briefs continue to state that no scan is executed.
- Tests cover Markdown and HTML brief output.
