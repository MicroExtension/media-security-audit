# Sprint 266 - Controlled Test Decision Center

## Goal

Make the session dashboard decide whether a mission is ready for a controlled
real-world pilot test before any technician launches checks at a customer site.

## Scope

- Add a controlled test decision model to the session dashboard.
- Summarize authorization, approved scope, selected services, executable checks,
  and prepared commands.
- Show blockers and points of attention with direct links to the safe review
  sections.
- Keep the decision conservative when runs already exist or some checks remain
  blocked.
- Update tests and documentation.

## Safety

- No scanner execution changes.
- No brute force, exploitation, payload, or credential attack flow.
- No external network dependency.
- The gate only summarizes stored mission preparation, scan plan, and run
  metadata.

## Acceptance Criteria

- Session dashboards expose a controlled test decision section.
- Missing authorization, scope, selected checks, executable checks, or commands
  block the pilot decision.
- Existing results or blocked/failed checks produce a warning decision.
- Ready sessions link technicians to the execution queue.
- Unit tests pass.
