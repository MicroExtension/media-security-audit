# Sprint 235 - Real Condition Test Runbook

## Goal

Make the first controlled customer pilot reproducible with a single runbook.

## Scope

- Add a real condition test runbook under `docs/`.
- Cover VM update, readiness, UI access, guided audit creation, guarded checks, finding review, report generation, closeout, and go/no-go criteria.
- Link the runbook from deployment documentation.
- Keep the runbook procedural only.
- Do not add scanner execution or package installation automation.

## Acceptance Criteria

- The runbook tells a technician how to conduct the first controlled pilot.
- The runbook repeats authorization, approved scope, customer window, and pause requirements.
- Tests verify the runbook and documentation links.

## Safety

- No scan execution added.
- No network activity added.
- No authorization bypass added.
