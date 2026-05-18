# Sprint 90 - Deployment Healthcheck Details

## Goal

Make the local appliance healthcheck more useful for Docker and VM deployments
without exposing customer data.

## Scope

- Add a pure healthcheck helper for data and reports directory readiness.
- Return structured `/healthz` payloads from the web app.
- Return HTTP 503 when a critical storage path is blocked.
- Add unit tests without requiring FastAPI in the test runtime.
- Update product and deployment notes.

## Acceptance Criteria

- Health payload includes overall status and coarse storage check statuses.
- Health payload does not include absolute filesystem paths.
- Blocked storage returns a failing health status code.
- Existing Docker healthcheck command remains compatible.

## Safety

- This sprint only changes local service health reporting.
- No scanner execution is added.
- No network scan activity is added.
