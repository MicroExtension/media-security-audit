# Sprint 11 - Web Mission Setup Updates

## Goal

Allow technicians to update mission setup details from the local web UI so a
blocked mission can be corrected without using the CLI.

## Scope

1. Add a mission setup form to the mission page.
2. Allow updates to mission name, audit type, authorization reference, and
   notes.
3. Recompute mission status after updates.
4. Keep scan execution CLI-only.
5. Add tests for form handling and mission view data.

## Safety Constraints

- No scan execution route in the web application.
- Mission updates require existing web authentication.
- Mission updates require form token validation.
- Authorization tracking is metadata only; it does not execute a scanner.

## Acceptance Criteria

- A mission without authorization can receive an authorization reference from
  the mission page.
- Mission status is recomputed after mission setup updates.
- Existing mission scope and findings are preserved.
- Unit tests cover mission setup update behavior.
