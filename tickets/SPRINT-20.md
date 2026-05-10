# Sprint 20 - Mission Export Package

## Goal

Allow technicians to generate a controlled ZIP package for a mission handoff or
archive without manually collecting JSON and report files.

## Scope

1. Add a mission export package helper.
2. Include client, mission, findings, activity, and scan run JSON.
3. Include already generated JSON, Markdown, and HTML reports when present.
4. Add mission page controls to generate and download the package.
5. Add tests for package contents and mission view links.

## Safety Constraints

- No scan execution route in the web application.
- No arbitrary file path is accepted from the browser.
- Package contents are built from known mission storage and known report paths.
- Raw scanner evidence is not bundled until evidence retention rules are defined.

## Acceptance Criteria

- Mission pages can generate a ZIP package.
- The ZIP contains a manifest and mission-local JSON data.
- Existing generated reports are included.
- Missing packages return a named error.
- Unit tests cover package generation and link rendering.
