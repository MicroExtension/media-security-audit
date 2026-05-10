# Sprint 22 - Authorization Brief Export

## Goal

Generate a pre-audit authorization brief that technicians can review before a
guarded CLI scan is executed.

## Scope

1. Add Markdown and HTML authorization brief rendering.
2. Include mission metadata, structured authorization details, selected checks,
   scope summary, approved scope, excluded scope, and draft scope.
3. Show whether the mission is ready for guarded CLI execution.
4. Add mission page controls to generate and download the brief.
5. Include generated authorization briefs in mission ZIP export packages.
6. Add tests for rendering, listing, missing files, mission view links, and ZIP
   packaging.

## Safety Constraints

- No scan execution is added to the browser.
- Brief generation is a file export only.
- Existing scan blockers are not weakened.
- Authorization reference and approved scope remain the hard blockers for
  guarded CLI execution.

## Acceptance Criteria

- A mission page can generate Markdown and HTML authorization briefs.
- The brief clearly states ready or not ready status.
- Missing authorization or approved scope is visible as a blocker.
- Generated briefs are downloadable and included in mission ZIP exports.
- Unit tests cover the new workflow without network activity.
