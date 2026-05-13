# Sprint 48 - Mission Readiness Action Links

## Goal

Make mission preparation easier to operate from the mission page by linking
readiness cards directly to the section that needs technician action.

## Scope

- Add optional action labels and anchors to mission readiness items.
- Link blocked or warning readiness cards to mission setup, scope, check
  selection, findings, or reports.
- Keep scan execution CLI-only.
- Update tests and documentation.

## Acceptance Criteria

- Authorization blockers link to mission setup.
- Scope blockers link to scope review.
- Check selection blockers link to check selection.
- Finding review warnings link to findings.
- Report warnings link to report generation.
- Existing readiness and scan plan behavior remains unchanged.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The web UI continues to expose scan planning only.
