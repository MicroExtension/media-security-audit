# Sprint 29 - Template-Assisted Mission Creation

Goal: Let technicians create a mission from a built-in audit template so the
initial audit type and check selection are consistent with the chosen workflow.

## Scope

1. Store the optional audit template id on missions.
2. Add a template selector to the dashboard mission creation form.
3. Apply the selected template audit type and recommended checks at mission
   creation time.
4. Show the template source in dashboard rows and mission setup details.
5. Preserve the existing manual mission creation path.
6. Add tests for template lookup, form handling, model storage, and web views.

## Safety

- No scanner execution.
- No network activity.
- No automatic scope creation.
- Check selection remains planning only and can be edited after mission creation.

## Acceptance Criteria

- A mission can be created without a template as before.
- A mission created with a known template stores the template id.
- Template-created missions inherit the template audit type and recommended
  checks.
- Unknown template ids are rejected.
- Dashboard and mission views expose the chosen template name.
