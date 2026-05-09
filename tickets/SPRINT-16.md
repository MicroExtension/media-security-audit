# Sprint 16 - Mission Activity Log

## Goal

Record and display key mission workflow actions so technicians have a local
trace of web changes made during an audit.

## Scope

1. Add an `ActivityEvent` domain model.
2. Store mission activity events in local JSON files.
3. Record web actions for mission updates, scope changes, finding changes, and
   report generation.
4. Show mission activity on the mission page.
5. Add tests for event storage and mission view output.

## Safety Constraints

- No scan execution route in the web application.
- No live network requests.
- Activity events are local audit metadata only.
- Existing mission, finding, and report outputs remain unchanged.

## Acceptance Criteria

- Activity events are persisted per mission.
- Mission pages display recorded activity in reverse chronological order.
- Web mutation routes record clear action summaries.
- Unit tests cover event storage and rendering data.
