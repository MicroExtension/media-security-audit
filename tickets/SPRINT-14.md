# Sprint 14 - Web Manual Finding Edits

## Goal

Allow technicians to correct structured manual findings from the local web UI
without recreating them, while keeping scanner-produced findings protected from
accidental evidence edits.

## Scope

1. Add web form handling for manual finding edits.
2. Add manual finding edit forms on the mission page.
3. Preserve finding review status and review notes during edits.
4. Reject scanner-produced finding edits from this form.
5. Add unit tests for manual finding edits and scanner edit rejection.

## Safety Constraints

- No scan execution route in the web application.
- No live network requests.
- Scanner findings remain review-only in this sprint.
- Manual finding edits must keep proof, risk, remediation, and counter-test
  fields required.

## Acceptance Criteria

- A technician can update a manual finding from the mission page.
- Review status and review notes are preserved.
- Scanner findings cannot be edited through the manual finding edit form.
- Unit tests cover successful and rejected edit paths.
