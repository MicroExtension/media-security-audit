# Sprint 56 - Dashboard Client Risk Summary

## Goal

Show client-level risk summaries in the dashboard client table so technicians can
prioritize customers without opening each client detail page.

## Scope

- Add active finding count, active high/critical count, risk score, and risk
  level to client row view models.
- Reuse the existing report risk scoring logic.
- Display the summary in the dashboard client table.
- Update tests and documentation.

## Acceptance Criteria

- Client rows expose active finding counts.
- Client rows expose active high/critical finding counts.
- Client rows expose risk score and risk level.
- False positives are excluded from the active risk summary.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
