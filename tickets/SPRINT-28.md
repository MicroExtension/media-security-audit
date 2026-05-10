# Sprint 28 - Audit Template Library

Goal: Start a built-in audit template library so technicians can plan repeatable
MSP audit missions without rebuilding the same methodology by hand each time.

## Scope

1. Add structured built-in audit templates for common MSP workflows.
2. Include recommended checks, scope guidance, authorization requirements, and
   expected deliverables.
3. Add a protected web page for browsing templates.
4. Support query and audit type filtering.
5. Add navigation from the main web layout.
6. Add unit tests for template structure, filtering, and web view construction.

## Safety

- No scanner execution.
- No network activity.
- No mission mutation from the template page.
- Templates are planning aids only in this sprint.

## Acceptance Criteria

- The application exposes at least four repeatable audit templates.
- Templates include recommended checks and authorization requirements.
- The web page can filter templates by query and audit type.
- Tests cover structure and view model behavior.
