# Sprint 234 - Scan Launch Trial Guardrails

## Goal

Make real pilot execution safer by showing live trial guardrails in the mission
Scan Launch Center.

## Scope

- Add a visible live-trial guardrail panel before service launch details.
- Remind technicians about the customer window, contact, monitoring, pause path,
  and final exports.
- Keep the guardrails informational.
- Do not change scanner execution.
- Do not change launch forms or authorization rules.

## Acceptance Criteria

- The Scan Launch Center shows live trial guardrails.
- The guardrails are covered by template and CSS tests.
- The page still uses the existing per-service guarded execution flow.

## Safety

- No scan execution added.
- No network activity added.
- No authorization bypass added.
