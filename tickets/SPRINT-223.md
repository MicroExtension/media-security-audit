# Sprint 223 - Run Monitor Follow-Up Cards

Status: implemented.

## Goal

Make recorded scan execution easier to understand from the mission page.

## Scope

- Add per-run follow-up cards above the technical run table.
- Show the service label, status, outcome title, and technician summary.
- Show command, finding, and evidence counters for each run.
- Surface run errors in a readable block.
- Link each run to the next useful action: review error, review findings, or
  generate reports.
- Keep the existing run table for detailed technical review.

## Out of Scope

- Do not add new scanners.
- Do not change guarded scan execution.
- Do not bypass authorization, scope, or explicit confirmation requirements.
- Do not add brute force, exploitation, payload, or exfiltration features.

## Acceptance Criteria

- Mission pages show a readable card for each stored scan run.
- Empty missions still show a clear no-run state.
- Existing run table data remains visible.
- Existing tests continue to pass.
