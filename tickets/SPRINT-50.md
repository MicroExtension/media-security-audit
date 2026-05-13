# Sprint 50 - Report Finding Dispositions

## Goal

Make reviewed finding decisions visible in generated reports so accepted risks
and false positives remain explainable after export.

## Scope

- Add status counts to the report summary.
- Add disposition notes to the JSON report summary.
- Add a Finding Dispositions section to Markdown and HTML reports.
- Show review notes in detailed Markdown and HTML finding blocks.
- Update tests and documentation.

## Acceptance Criteria

- JSON summaries include counts for every finding status.
- JSON summaries include reviewed disposition notes.
- Markdown reports include disposition counts and notes.
- HTML reports include disposition counts and notes.
- Active risk scoring continues to exclude false positives.

## Safety

- No live scanner execution is added.
- No network activity is added.
- Reporting remains based only on stored mission data and findings.
