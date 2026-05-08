# Sprint 8 - Finding Review Workflow

## Goal

Allow technicians to review findings from the local web UI so reports can
reflect confirmed items and false positives without manual JSON edits.

## Scope

1. Add JSON store helpers to get and update individual findings.
2. Add finding status update form on mission detail pages.
3. Persist optional review notes in finding metadata.
4. Keep review mutation routes authenticated and protected by form tokens.
5. Add unit tests for storage and form behavior.

## Safety Constraints

- No scan execution from the browser.
- Review updates must not alter proof, risk, remediation, or counter-test text.
- False positives remain excluded from active report metrics by existing report logic.
- Mutation routes must require authentication and form token validation.

## Acceptance Criteria

- A technician can change a finding status from the mission page.
- A technician can attach a short review note.
- Stored findings retain the updated status across reloads.
- Unit tests cover status updates and review note persistence.
