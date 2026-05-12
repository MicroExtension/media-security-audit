# Sprint 37 - Activity Client And Mission Filters

Goal: Let operators narrow the workspace activity log to a specific client or
mission when reviewing operational history.

## Scope

1. Add client and mission filters to the Activity page.
2. Preserve selected client and mission filters in export links.
3. Include `client_id` and `mission_id` filter metadata in JSON exports.
4. Include `client_id` in each exported event row.
5. Add tests for filtered views and filtered exports.

## Safety

- No scanner execution.
- No network activity.
- No mutation of missions, findings, reports, scope, or events.
- Filtering is read-only and uses stored activity events.

## Acceptance Criteria

- The Activity page can filter by client and mission.
- Export links preserve client and mission filters.
- Filtered JSON exports include visible count, total count, client id, and
  mission id.
- Tests verify filtered rows and exported event metadata.
