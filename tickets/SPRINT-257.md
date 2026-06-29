# Sprint 257 - Wizard Final Readiness

## Goal

Make the final guided audit review easier to understand before the technician
creates the audit mission.

## Scope

- Add a final ready/blocked decision panel to the validation step.
- Show client, mission, target, and service counters in one compact summary.
- Show the remaining blockers when audit creation is not ready.
- Explain the next steps after creation: console, scan plan, explicit launch,
  and reports/remediation follow-up.
- Keep the existing creation checklist and submit button gates unchanged.

## Safety

- No scan execution is added.
- No authorization bypass is added.
- The submit button remains blocked by the existing client, mission, scope,
  service coverage, and credential guardrail checks.

## Acceptance

- The final review displays a ready/blocked state.
- Missing prerequisites are summarized clearly.
- The panel updates live with the wizard snapshot.
- Unit tests cover the template, CSS, and JavaScript hooks.
