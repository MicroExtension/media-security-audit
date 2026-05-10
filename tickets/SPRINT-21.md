# Sprint 21 - Structured Authorization Details

## Goal

Make written authorization easier to track from the mission workflow and include
the relevant authorization metadata in mission reports.

## Scope

1. Add optional authorization contact, date, expiration date, emergency contact,
   report recipients, and evidence retention fields to missions.
2. Support the fields from CLI mission creation.
3. Support editing the fields from mission setup pages.
4. Include the fields in JSON, Markdown, and HTML reports.
5. Add tests for validation, rendering, and mission views.

## Safety Constraints

- Authorization reference remains the scan gating signal.
- Structured metadata does not weaken existing scan guards.
- Web UI still does not launch scans.
- Evidence retention is metadata only; it does not delete or collect files.

## Acceptance Criteria

- Existing mission data remains compatible.
- New authorization fields are optional.
- Negative evidence retention values are rejected.
- Mission reports show the authorization metadata.
- Tests cover CLI, web forms, web views, models, and report output.
