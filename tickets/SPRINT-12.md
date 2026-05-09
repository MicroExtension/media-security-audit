# Sprint 12 - Web Scope Review

## Goal

Allow technicians to review and correct mission scope from the local web UI
before any guarded scanner execution happens in the CLI.

## Scope

1. Add storage support for updating an existing scope item.
2. Add web form handling for scope updates.
3. Add mission page forms for each stored scope item.
4. Allow updates to type, value, environment, notes, approved, and excluded
   state.
5. Add tests for status recomputation and invalid scope rejection.

## Safety Constraints

- No scan execution route in the web application.
- Scope updates require existing web authentication.
- Scope updates require form token validation.
- A scope item cannot be both approved and excluded.
- Scope value validation must run again during updates.

## Acceptance Criteria

- A technician can approve or exclude existing scope from the mission page.
- Mission status is recomputed after scope updates.
- Invalid scope values are rejected.
- Unit tests cover valid and invalid scope update paths.
