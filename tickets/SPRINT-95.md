# Sprint 95 - Preflight Action Hints

## Goal

Make deployment preflight results directly actionable for technicians installing
the appliance on customer VMs.

## Scope

- Add a short remediation action to each preflight item.
- Include actions in JSON output for install scripts.
- Show action lines in text output only when an item needs attention.
- Update tests and deployment documentation.

## Acceptance Criteria

- Ready checks do not add noise to text output.
- Warning, missing, and blocked checks provide a clear next action.
- JSON preflight items include an `action` field.
- No scanner command is executed.

## Safety

- This sprint only changes local preflight formatting and guidance.
- No scanner execution is added.
- No network activity is added.
