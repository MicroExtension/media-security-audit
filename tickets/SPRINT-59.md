# Sprint 59 - Dashboard Client Risk Level Summary

## Goal

Show client-level risk level counts on the dashboard so MSP technicians can see
the portfolio risk distribution without opening each client.

## Scope

- Add client risk summary rows to the dashboard view model.
- Count risk once per client from the existing client risk level.
- Display critical, high, medium, low, and none counts.
- Update tests and documentation.

## Acceptance Criteria

- Dashboard exposes client risk level counts.
- Counts are scoped to clients, not missions or raw findings.
- Summary display reuses existing non-interactive dashboard components.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard summary data.
