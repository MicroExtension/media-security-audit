# Sprint 229 - Guided Target Coverage Validation

Status: implemented.

## Goal

Prevent guided audit creation when selected services do not have compatible
target coverage.

## Scope

- Share audit check target requirements between UI and form validation.
- Validate guided audit selected checks against generated scope items.
- Reject HTTP header checks without URL scope.
- Reject DNS/Mail checks without domain scope.
- Add regression tests and update documentation.

## Out of Scope

- Do not run scans.
- Do not change guarded scan execution.
- Do not add external lookups.
- Do not change report generation.

## Acceptance Criteria

- Guided audit creation fails before client or mission storage when service
  selections lack matching target types.
- Existing valid guided audit forms still create client, mission, and approved
  scope.
- Existing wizard UI coverage remains aligned with server validation.
- Existing tests continue to pass.
