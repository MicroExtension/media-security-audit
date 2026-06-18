# Sprint 221 - Guided Audit Stepper UX

Status: implemented.

## Goal

Make audit creation understandable for a MEDIA technician opening the web UI for
the first time.

## Context

Pilot feedback shows that the current interface is functional but still too
dense. Audit creation must become a true step-by-step assistant instead of a
long form with many sections visible at once.

## Scope

- Convert guided audit creation into a focused stepper flow.
- Add Previous and Next controls between setup steps.
- Keep a visible progress indicator.
- Validate each step before allowing the technician to continue.
- Keep a compact summary visible for client, mission, targets, services, and
  authorization readiness.
- Keep final creation disabled until authorization, approved scope, and selected
  checks are present.
- Use clear operational wording for missing information.

## Out of Scope

- Do not change scanner execution behavior.
- Do not add brute force, exploitation, payload, or exfiltration features.
- Do not change CVE/KEV scanner policy in this sprint.

## Acceptance Criteria

- A technician can create a client audit by following one visible step at a
  time.
- The UI has clear Previous and Next controls.
- Required fields block progression with a plain explanation.
- The final review shows client, audit type, authorization, approved scope, and
  selected services.
- Existing tests continue to pass.
