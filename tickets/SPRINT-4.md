# Sprint 4 - Local Web UI Foundation

## Objective

Create the first local web interface using the existing domain and reporting
engine.

## Scope

Implement:
- FastAPI app
- Jinja2 templates
- dashboard page
- client list page
- mission list page
- mission creation wizard skeleton
- scope management page
- findings review page using fixture data
- report generation page

Do not implement live scanner execution in this sprint unless the CLI scanner
foundation is already stable.

## UI Rules

- no scan action without approved scope
- no destructive options
- every mission page shows authorization status
- every report page warns about unreviewed critical/high findings
- false positive and accepted risk actions require notes

## Acceptance Criteria

- local web app starts on port 8080
- dashboard loads
- a mission can be created from the UI
- scope items can be added and validated
- fixture findings can be reviewed
- reports can be generated through the UI
- unit or integration tests cover main routes

