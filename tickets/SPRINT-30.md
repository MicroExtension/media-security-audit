# Sprint 30 - Mission Template Guidance

Goal: Show the selected audit template guidance on mission pages so technicians
can prepare scope, authorization, and deliverables without switching back to
the template library.

## Scope

1. Add mission view model data for selected template guidance.
2. Show template summary and recommended checks on mission pages.
3. Show scope guidance, authorization requirements, and expected deliverables.
4. Keep missions without templates unchanged.
5. Add unit tests for template guidance presence and absence.

## Safety

- No scanner execution.
- No network activity.
- No mission mutation.
- Template guidance is read-only and planning-only.

## Acceptance Criteria

- A mission with a known template shows template guidance in the mission view.
- A mission without a template has no guidance block.
- Guidance includes recommended checks, scope, authorization, and deliverables.
- Tests cover the view behavior.
