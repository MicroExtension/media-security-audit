# Sprint 76 - Activity Filter Context

## Goal

Make filtered activity views self-explanatory so technicians can see which
context they are reviewing and quickly jump back to related client or mission
pages.

## Scope

- Add active filter summary data to activity log views.
- Link selected client and mission filters back to their context pages.
- Add a clear filters action.
- Update tests and product notes.

## Acceptance Criteria

- Unfiltered activity views do not show an active filter summary.
- Filtered activity views expose active filter chips.
- Client and mission filter chips link to their respective pages when known.
- Clearing filters links back to the unfiltered Activity page.

## Safety

- This sprint only changes read-only web navigation and display data.
- No scanner execution is added.
- No network activity is added.
