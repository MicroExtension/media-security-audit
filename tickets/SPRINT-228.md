# Sprint 228 - Wizard Service Target Coverage

Status: implemented.

## Goal

Help technicians understand whether the selected audit services have matching
target inputs before creating an audit.

## Scope

- Expose required scope types for each guided wizard check.
- Add a Target Coverage section to the wizard checks step.
- Show selected checks as ready or missing based on entered target types.
- Infer target types from wizard inputs without running scanners.
- Update tests and documentation.

## Out of Scope

- Do not execute scans.
- Do not change guarded scan execution requirements.
- Do not change mission storage behavior.
- Do not perform external lookups.

## Acceptance Criteria

- The guided wizard displays service-to-target coverage for selected checks.
- HTTP requires URL coverage.
- DNS/Mail requires domain coverage.
- SMB and LDAP require host, IP, or domain-style coverage.
- The existing creation checklist and submit guard remain unchanged.
- Existing tests continue to pass.
