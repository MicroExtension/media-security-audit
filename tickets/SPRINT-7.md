# Sprint 7 - Web Workflow Forms

## Goal

Make the local web UI usable for the first mission setup workflow without
adding browser-triggered scanner execution.

## Scope

1. Add dashboard forms for client creation.
2. Add dashboard forms for mission creation.
3. Add mission detail form for scope creation.
4. Reuse existing domain models and JSON store validation.
5. Add success and error redirects.
6. Add anti-CSRF form token validation.
7. Add unit tests for form parsing and creation behavior.

## Safety Constraints

- No scan execution from the browser.
- Scope validation must stay identical to the CLI models.
- Approved and excluded scope cannot both be set.
- Authentication guards must apply to all mutation routes.
- Mutation routes must require a form token.

## Acceptance Criteria

- A technician can create a client from the dashboard.
- A technician can create a mission from the dashboard.
- A technician can add approved scope from the mission detail page.
- Invalid form submissions show an error and do not corrupt stored data.
- Unit tests cover the form helpers.
