# Sprint 255 - Wizard Target Coach

## Goal

Make the guided audit target step easier to understand by showing which target
fields are required for the currently selected check families.

## Scope

- Add a target coach panel to the guided audit target step.
- Show one card for internal targets, public domains, web URLs, and AD/LDAP.
- Mark cards as optional, required, ready, or missing based on selected checks
  and entered target lines.
- Add jump buttons that focus the matching target field.
- Keep the existing service coverage and final creation gates unchanged.

## Safety

- No scan execution is added.
- No target is generated automatically.
- No brute force, payload, exploitation, or credential attack behavior is added.
- The technician still must enter authorized targets and confirm scope.

## Acceptance

- Selecting quick profiles or checkboxes updates the target coach.
- Required target cards display ready/missing status and line counts.
- Jump buttons focus the matching target text area.
- Unit tests cover the new template, CSS, and JavaScript hooks.
