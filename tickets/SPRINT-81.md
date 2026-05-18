# Sprint 81 - Active Top Navigation

## Goal

Make the local web interface easier to orient by marking the active workspace
area in the top navigation.

## Scope

- Add active state logic to the shared base template.
- Treat dashboard, client, and mission pages as the main Dashboard workspace.
- Mark Activity, Templates, Remediations, and System routes independently.
- Add light styling for the active navigation item.
- Update tests and product notes.

## Acceptance Criteria

- The shared top navigation exposes an active item for each major route group.
- Active navigation items include `aria-current="page"`.
- Styling remains consistent with the existing restrained web UI.
- No route behavior changes are introduced.

## Safety

- This sprint only changes read-only web navigation.
- No scanner execution is added.
- No network activity is added.
