# Sprint 38 - Activity Date Filters

Goal: Let operators narrow the workspace activity log to an inclusive date
range for easier operational review.

## Scope

1. Add `From` and `To` date filters to the Activity page.
2. Preserve selected date filters in export links.
3. Include `date_from` and `date_to` filter metadata in JSON exports.
4. Include each event `created_date` in JSON exports.
5. Add tests for date-filtered views and exports.

## Safety

- No scanner execution.
- No network activity.
- No mutation of missions, findings, reports, scope, or events.
- Filtering is read-only and uses stored activity events.

## Acceptance Criteria

- The Activity page can filter by an inclusive date range.
- Export links preserve selected date filters.
- Filtered JSON exports include visible count, total count, date range, and
  event dates.
- Tests verify filtered rows and exported date metadata.
