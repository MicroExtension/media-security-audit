# Sprint 241 - VM Test Readiness Center

## Goal

Prepare one clean operator entry point for updating the VM, validating the
local web UI, and capturing pilot feedback before a real-condition test.

## Scope

1. Add a dedicated `/test-readiness` web page.
2. Add copyable VM update and smoke test commands.
3. Add a non-destructive Debian VM UI smoke test report script.
4. Document the VM update and test procedure.
5. Add tests that keep the workflow scanner-free, secret-free, and log-free.

## Acceptance Criteria

- The top navigation exposes `Test VM`.
- The test readiness page links to System, Pilot, New Guided Audit, Clients,
  Audits, and Exports.
- The page includes the VM update command, smoke test command, SSH tunnel
  command, and browser checklist.
- `scripts/debian-vm-ui-smoke-test.sh` writes a local report under
  `reports/test-readiness`.
- The smoke test does not launch scanner commands, install packages, collect
  application logs, or print secrets.
- Tests cover the page, CSS, script, README, and deployment documentation.
