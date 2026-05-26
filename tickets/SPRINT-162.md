# Sprint 162 - Web Mission Export Inventory

## Goal

Let technicians review mission export ZIP package readiness from the web
interface without opening each mission or using the CLI.

## Scope

- Add a `/exports` page.
- Add export inventory navigation.
- Show package summary counts.
- Show mission, client, status, detail, package size, and integrity counters.
- Link to the mission, client, and ZIP download when a package exists.
- Keep missing mission packages visible by default with a toggle.
- Update tests and documentation.

## Out Of Scope

- No scanner execution.
- No report regeneration.
- No package mutation.
- No archive extraction workflow.
- No customer network activity.

## Acceptance Criteria

- The web UI exposes a mission export inventory page.
- Existing packages show integrity status and download links.
- Missing packages can be shown or hidden.
- The page does not generate scans, reports, or packages.
