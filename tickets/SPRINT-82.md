# Sprint 82 - Keyboard Skip Link

## Goal

Improve keyboard accessibility across the local web interface by adding a
shared skip link to jump directly to the main content.

## Scope

- Add a skip link to the shared base template.
- Add a stable `main-content` anchor to the main layout region.
- Style the skip link so it appears only when focused.
- Update tests and product notes.

## Acceptance Criteria

- Every web page using the shared base layout exposes a skip link.
- The skip link targets the main content region.
- The main content region can receive focus.
- Existing navigation and route behavior remain unchanged.

## Safety

- This sprint only changes shared web layout accessibility.
- No scanner execution is added.
- No network activity is added.
