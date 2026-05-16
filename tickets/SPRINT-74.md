# Sprint 74 - Mission Context Links

## Goal

Add contextual links to mission detail pages so technicians can quickly open
the parent client page and the filtered mission activity log.

## Scope

- Add a mission activity log URL to the mission view model.
- Add mission header links for the parent client and filtered activity.
- Keep the existing live HTML report action.
- Add light styling for grouped page actions.
- Update tests and documentation.

## Acceptance Criteria

- Mission pages expose an Open Client action.
- Mission pages expose an Activity Log action filtered by mission ID.
- Existing Live HTML report action remains available.
- Tests cover the generated mission activity URL and template links.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only navigation links.
