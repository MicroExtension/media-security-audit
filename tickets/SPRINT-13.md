# Sprint 13 - Web Manual Findings

## Goal

Allow technicians to add structured manual findings from the local web UI so
reports can be produced from field observations before or alongside scanner
results.

## Scope

1. Add web form handling for manual finding creation.
2. Add a mission page form for title, severity, asset, category, proof, risk,
   remediation, counter-test, and confidence.
3. Store manual findings through the existing finding engine.
4. Keep scanner execution CLI-only.
5. Add tests for valid and invalid manual finding input.

## Safety Constraints

- No scan execution route in the web application.
- No live network requests.
- Manual findings require proof, risk, remediation, and counter-test text.
- Manual findings must use the normalized finding model.

## Acceptance Criteria

- A technician can add a manual finding from the mission page.
- The finding appears in the existing findings list and reports.
- Invalid or incomplete manual findings are rejected.
- Unit tests cover manual finding form behavior.
