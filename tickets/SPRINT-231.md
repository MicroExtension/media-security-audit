# Sprint 231 - Wizard Missing Target Actions

Status: implemented.

## Goal

Make missing target coverage easier to correct from the guided audit wizard.

## Scope

- Add action buttons to missing service coverage cards.
- Route missing HTTP coverage to Web URLs.
- Route missing DNS/Mail coverage to Public Domains.
- Route missing LDAP coverage to AD / LDAP Servers.
- Route missing SMB and Nmap coverage to Internal Networks, IPs, Hosts.
- Update tests and documentation.

## Out of Scope

- Do not execute scans.
- Do not change server-side validation.
- Do not change mission storage behavior.
- Do not add external network activity.

## Acceptance Criteria

- Missing coverage cards show a targeted correction action.
- Clicking a missing coverage action opens the target step and focuses the
  matching field.
- Existing wizard coverage guards remain active.
- Existing tests continue to pass.
