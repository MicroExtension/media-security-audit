# Sprint 39 - Activity CSV Export

Goal: Add a CSV export to the workspace activity log so operators can review
filtered events in spreadsheet tools.

## Scope

1. Add an activity-specific export format enum.
2. Preserve existing JSON, Markdown, and HTML activity exports.
3. Add CSV export links to the Activity page.
4. Export event id, client, mission, action, summary, timestamps, and metadata.
5. Add tests for CSV output and export links.

## Safety

- No scanner execution.
- No network activity.
- No mutation of missions, findings, reports, scope, or events.
- CSV generation reads filtered activity events only.

## Acceptance Criteria

- The Activity page exposes a CSV export link.
- CSV exports preserve the currently filtered event set.
- CSV rows include client, mission, action, timestamp, and metadata columns.
- Tests verify CSV filename, media type, and parsed row contents.
