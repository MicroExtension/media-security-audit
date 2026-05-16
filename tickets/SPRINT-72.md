# Sprint 72 - Mission Page Shortcuts

## Goal

Add shortcut links to mission detail pages so technicians can jump directly to
the main mission workflow sections.

## Scope

- Add mission page shortcuts below mission metrics.
- Add stable anchors for readiness, scan plan, run monitor, activity, and
  counter-test sections.
- Reuse existing anchors for checks, setup, reports, scope, and findings.
- Show simple counts from the existing mission view model.
- Update tests and documentation.

## Acceptance Criteria

- Mission pages expose shortcut links to all major workflow sections.
- Shortcuts use stable static anchors and do not require JavaScript.
- Shortcut badges use already loaded mission view data.
- Tests cover shortcut anchors and badge expressions.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only navigation links.
