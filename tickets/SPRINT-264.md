# Sprint 264 - Session Finding Explainers

## Goal

Make session findings easier to understand before customer restitution by adding
plain-language explainer cards to the session dashboard.

## Scope

- Add a session finding explainer model.
- Generate concise explanations from stored findings.
- Show severity, status, affected asset, plain explanation, impact, remediation,
  and validation guidance.
- Keep remediation priorities available as the action board below the explainers.
- Update tests and documentation.

## Safety

- No scanner execution changes.
- No brute force, exploitation, payload, or credential attack flow.
- No external network dependency.
- Explanations are generated from stored finding data only.

## Acceptance Criteria

- The session dashboard template exposes finding explainer cards.
- High-priority findings show a clear impact and remediation path.
- Empty sessions still render a safe empty state.
- Existing client brief, progress, result explorer, timeline, and remediation
  priority behavior remains unchanged.
- Unit tests pass.
