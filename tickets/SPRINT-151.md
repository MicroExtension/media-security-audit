# Sprint 151 - Consolidated Scan Plan Summary

## Goal

Expose one read-only CLI command that summarizes every selected audit check
before any scanner execution is considered.

## Scope

- Add `scan plan-all`.
- Reuse the safe scan plan previews already used by the web UI.
- Support technician-friendly text output.
- Support machine-readable JSON output.
- Include mission status, authorization state, approved scope count, ready and
  blocked check counts, and planned command previews.
- Mark the command output as `execution=not_executed`.

## Out Of Scope

- No scanner execution.
- No browser scan launch controls.
- No new scanner adapter.
- No customer network activity.

## Acceptance Criteria

- `scan plan-all` works with text output.
- `scan plan-all --format json` returns schema-versioned JSON.
- The command never creates scan run records.
- Tests cover selected Nmap, HTTP, DNS/Mail, TLS, SMB, and LDAP checks.
- Documentation shows the command in the local workflow.
