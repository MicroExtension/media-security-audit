# Sprint 36 - Activity Log Filters

Goal: Make the workspace activity log easier to use as the number of missions
and events grows.

## Scope

1. Add search text filtering for activity rows.
2. Add action filtering based on recorded event actions.
3. Preserve active filters in JSON, Markdown, and HTML export links.
4. Include filter metadata in exported activity logs.
5. Add tests for filtered views and filtered exports.

## Safety

- No scanner execution.
- No network activity.
- No mutation of missions, findings, reports, scope, or events.
- Filtering is read-only and uses stored activity events.

## Acceptance Criteria

- The Activity page has search and action filters.
- Export links preserve the selected filters.
- Filtered JSON exports include visible count, total count, query, and action.
- Tests verify filtered rows and filtered export metadata.
