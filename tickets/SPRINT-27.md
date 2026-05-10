# Sprint 27 - Remediation Library Export

Goal: Allow technicians to export the visible remediation library so standard
guidance can be included in audit handoff files, internal reviews, or customer
preparation notes.

## Scope

1. Keep the Remediations page filterable by query and category.
2. Add read-only export links for JSON, Markdown, and HTML.
3. Preserve the active query and category filters in each export.
4. Include risk, remediation, counter-test, severity, effort, category, and
   applicability fields in each export.
5. Add unit tests for filtered export rendering.

## Safety

- No scanner execution.
- No network activity.
- No customer data access.
- No mutation of remediation entries from the web UI.
- Exports are generated from the built-in remediation library only.

## Acceptance Criteria

- A filtered remediation library view exposes JSON, Markdown, and HTML export
  links.
- Export content includes only entries matching the active filters.
- Generated filenames are deterministic.
- Tests cover export links and output content.
