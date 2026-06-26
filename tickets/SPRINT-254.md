# Sprint 254 - Guided Audit Quick Profiles

## Goal

Make the guided audit wizard easier to start by adding quick audit profiles that
preselect the audit mode and safe check families before the technician enters
authorized targets.

## Scope

- Add visible quick profile cards above the wizard form.
- Cover internal LAN, external web/mail, AD/LDAP, and full safe review starts.
- Apply the selected profile client-side by updating the audit type and selected
  checks only.
- Move the technician to the target step after applying a profile.
- Keep the existing service coverage, authorization, and final validation gates.

## Safety

- No scan execution is added.
- No brute force, payload, exploitation, or credential attack behavior is added.
- Profiles only prepare mission metadata and selected safe checks.

## Acceptance

- The wizard exposes quick profile cards with explicit check mappings.
- Applying a profile updates selected checks and the audit type.
- The wizard still requires authorized targets and scope confirmation before
  audit creation.
- Unit tests cover the new template, CSS, and JavaScript hooks.
