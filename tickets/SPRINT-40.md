# Sprint 40 - Client Detail Page

Goal: Add a client-focused web page so operators can review one client's audit
history without scanning the whole dashboard.

## Scope

1. Add a `ClientView` model with client metadata, mission rows, and risk
   metrics.
2. Add `/clients/{client_id}` route.
3. Link client names from the dashboard mission and client tables.
4. Add a `client.html` template showing mission history and client metrics.
5. Add tests for client metrics and mission isolation.

## Safety

- No scanner execution.
- No network activity.
- No mutation of clients, missions, findings, scope, reports, or events.
- The page reads existing local JSON data only.

## Acceptance Criteria

- Dashboard client names link to the client detail page.
- The client detail page lists only that client's missions.
- Client metrics include missions, findings, high/critical findings, and
  approved scope.
- Tests verify a client page does not include another client's missions.
