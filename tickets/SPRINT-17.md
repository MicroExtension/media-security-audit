# Sprint 17 - Web Check Selection

## Goal

Allow technicians to select the safe audit checks planned for a mission before
any browser execution controls exist.

## Scope

1. Add selected audit checks to the mission model.
2. Keep the default selection aligned with current safe foundation modules.
3. Add a mission page form for selecting checks.
4. Filter scan plan previews according to selected checks.
5. Record check selection changes in mission activity.
6. Add tests for model defaults, form handling, readiness, and mission views.

## Safety Constraints

- No scan execution route in the web application.
- No live network requests.
- Check selection changes planning only.
- Empty selections must block preview planning rather than launching anything.

## Acceptance Criteria

- New missions default to Nmap, HTTP headers, and DNS/Mail checks.
- Mission pages show selected and unselected checks clearly.
- Scan plan previews only include selected checks.
- No selected checks produces a blocked readiness state.
- No selected checks prevents ready-to-scan mission status.
- Unit tests cover check selection behavior.
