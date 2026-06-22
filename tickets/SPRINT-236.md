# Sprint 236 - Pilot Real Condition Checklist

## Goal

Make the first real-condition customer test easier to run from the local Pilot
page instead of relying only on external documentation.

## Scope

- Add a structured real-condition trial checklist to the Pilot runbook view.
- Render the checklist on `/pilot`.
- Include the checklist in Pilot runbook Markdown and JSON exports.
- Keep the existing Pilot evidence bundle file list unchanged.
- Update tests and product notes.

## Acceptance Criteria

- The Pilot page shows a Real Condition Trial section.
- Pilot runbook Markdown includes the real-condition checklist.
- Pilot runbook JSON includes machine-readable real-condition items.
- Tests verify the template, view model, Markdown, JSON, and archived runbook.

## Safety

- No scanner execution added.
- No network activity added.
- No authorization bypass added.
