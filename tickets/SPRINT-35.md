# Sprint 35 - Workspace Activity Log Export

Goal: Provide a workspace-level activity log so appliance operators can review
and export mission workflow events.

## Scope

1. Add an `Activity` web page that aggregates mission activity events.
2. Show event counts, mission counts, client counts, and latest event rows.
3. Include client, mission, action, summary, timestamp, and metadata details.
4. Add JSON, Markdown, and HTML exports for the activity log.
5. Add unit tests for view generation and exports.

## Safety

- No scanner execution.
- No network activity.
- No mutation of missions, findings, reports, or scope.
- The activity page reads existing stored events only.

## Acceptance Criteria

- The web navigation includes an Activity page.
- The page lists activity events across missions.
- Activity log exports include the same event details.
- Tests verify sorting, metadata rendering, and export formats.
