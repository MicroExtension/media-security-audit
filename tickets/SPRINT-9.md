# Sprint 9 - Web Report Generation

## Goal

Allow technicians to generate persistent JSON, Markdown, and HTML reports from
the local web UI after reviewing findings.

## Scope

1. Add a web report export helper using the existing report renderer.
2. Add a configurable `--reports-dir` for the web server.
3. Add a mission-page report generation form.
4. Add controlled download links for generated report formats.
5. Update Docker to write reports into the mounted reports folder.
6. Add tests for persistent report generation and deployment defaults.

## Safety Constraints

- No scan execution from the browser.
- Report downloads must be selected by known report format, not arbitrary paths.
- Report generation must use stored mission findings only.
- Mutation route must require authentication and form token validation.

## Acceptance Criteria

- A technician can generate mission reports from the mission page.
- JSON, Markdown, and HTML files are written to the reports directory.
- Generated report links appear on the mission page after export.
- Docker uses `/var/lib/media-audit/reports` for web-generated reports.
- Unit tests cover report generation and missing report handling.
