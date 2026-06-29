# Sprint 256 - Wizard Service Coach

## Goal

Make the guided audit service step easier to operate by adding service presets
and a live ready/missing service coach.

## Scope

- Add service preset buttons for LAN, web/mail, directory, and full safe review.
- Let presets update selected checkboxes without launching any scan.
- Show a live service coach with selected controls, ready/missing status, and
  direct target-field actions.
- Keep existing target coverage and audit creation gates in place.

## Safety

- No scan execution is added.
- No brute force, payload, exploitation, or credential attack behavior is added.
- Presets only change selected safe check families in the wizard.

## Acceptance

- Service presets update selected checks.
- Service coach displays selected checks and compatible-target readiness.
- Missing services provide a direct action to the matching target field.
- Unit tests cover the template, CSS, and JavaScript hooks.
