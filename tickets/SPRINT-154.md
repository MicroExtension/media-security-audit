# Sprint 154 - CLI Mission Readiness

## Goal

Expose a read-only mission readiness check for technicians and automation before
guarded CLI execution.

## Scope

- Add a shared mission readiness payload.
- Reuse the same readiness items shown in the web UI.
- Include generated report count and scan plan summary.
- Add CLI `mission readiness`.
- Support text and JSON output.
- Support strict exit behavior for blocked or warning missions.

## Out Of Scope

- No scanner execution.
- No browser scan launch controls.
- No customer network activity.
- No change to existing scanner guardrails.

## Acceptance Criteria

- Blocked missions return a blocked readiness payload.
- Ready missions with reviewed findings and reports return ready.
- JSON output is machine-readable.
- Strict mode can fail automation on warnings or blockers.
- Tests prove no scan run records are created.
