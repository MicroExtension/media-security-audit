# Sprint 262 - Session Remediation Priority Board

## Goal

Make the session dashboard immediately useful after findings are available.

## Scope

- Add a remediation priority board to the session dashboard.
- Show the highest-priority active findings first.
- Include severity, status, affected asset, risk, remediation, and counter-test.
- Keep detailed finding editing on the mission page.

## Safety

- No scanner execution behavior is changed.
- No authorization, scope, or explicit launch guardrail is changed.
- The priority board is read-only and uses existing normalized findings.

## Acceptance

- The session dashboard exposes remediation priority cards.
- Priority cards are sorted by existing finding severity order.
- Each card gives the technician a clear risk, correction, and validation step.
- Tests cover the template, CSS, and computed priority data.
