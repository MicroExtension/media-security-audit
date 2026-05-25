# Sprint 150 - LDAP Basic Audit Foundation

## Goal

Add a guarded LDAP basic audit foundation for anonymous RootDSE checks without
running live LDAP traffic during development.

## Scope

- Add optional `ldap` audit check and labels.
- Build safe `ldapsearch` RootDSE plan commands for approved host, IP, or domain scope.
- Require `--execute`, mission authorization, and approved scope before any live LDAP run.
- Execute commands without shell invocation.
- Reject credentialed, file-driven, extended, and subtree command shapes.
- Parse fixture LDIF output into normalized LDAP findings.
- Store LDAP findings, evidence, and scan run metadata on missions.
- Add web scan plan previews for selected LDAP checks.
- Install `ldap-utils` in the Docker image for future appliance readiness.

## Acceptance Criteria

- `scan ldap-plan` prints planned `ldapsearch` commands only.
- `scan ldap-run` refuses to run without `--execute`.
- LDAP run tests use mocked runners only.
- Parsed LDAP findings include severity, proof, risk, remediation, and counter-test text.
- Mission scan plan previews show LDAP only when the LDAP check is selected.
- Existing default mission checks remain unchanged.

## Safety

- No live LDAP execution during development.
- No credentialed LDAP checks.
- No subtree directory enumeration.
- No file-driven LDAP queries.
- No LDAP controls or extensions.
- No browser-driven scan execution added.
- All command execution remains guarded and shell-free.
