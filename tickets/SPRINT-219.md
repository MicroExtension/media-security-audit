# Sprint 219 - Pilot Handoff Decision

## Goal

Show a clear Pilot handoff decision before the evidence bundle is delivered.

## Scope

- add a Pilot handoff decision model
- derive ready, warning, or blocked status from Pilot readiness
- show the decision and next action on the Pilot page
- include the decision in Pilot runbook JSON
- include the decision in Pilot readiness JSON and Markdown
- include the decision in Pilot handoff summary JSON and Markdown
- bump affected JSON schema versions
- cover visible, exported, and archived bundle behavior with tests

## Safety

- no scanner execution is added
- no network activity is added
- no bundle extraction or restore behavior is added
- the decision is computed from existing local readiness metadata

## Acceptance Criteria

- Pilot page exposes a handoff decision panel
- warning workspaces point technicians to attention items
- ready workspaces point technicians to the bundle download
- runbook, readiness, and handoff summary exports include the decision
- archived Pilot bundle exports preserve the same decision metadata
