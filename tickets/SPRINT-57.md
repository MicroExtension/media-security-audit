# Sprint 57 - Dashboard Client Risk Ordering

## Goal

Order dashboard client rows by operational priority and then by risk, so
technicians see the most urgent customers first when priorities are otherwise
equal.

## Scope

- Keep preparation priority as the first sort criterion.
- Use risk score, active high/critical findings, active findings, and new
  findings as tie-breakers.
- Add tests for equal-priority client ordering.
- Update documentation.

## Acceptance Criteria

- Blocked, warning, ready, and empty client priorities keep their existing
  precedence.
- Clients with the same preparation priority are ordered by highest risk first.
- Sorting is deterministic when risk is tied.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only changes read-only dashboard ordering.
