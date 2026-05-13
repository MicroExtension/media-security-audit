# Sprint 51 - Mission Finding Disposition Summary

## Goal

Show finding disposition counts directly on the mission page so technicians can
review status coverage before generating reports.

## Scope

- Reuse the report status counting logic in the web view model.
- Add mission page disposition counters for every finding status.
- Keep the existing finding review workflow unchanged.
- Update tests and documentation.

## Acceptance Criteria

- Mission pages expose counts for new, confirmed, false positive, accepted risk,
  remediated, counter-test passed, and counter-test failed findings.
- The web view uses the same status counts as report summaries.
- Existing report, finding review, and scan planning behavior remains unchanged.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only mission UI summary data.
