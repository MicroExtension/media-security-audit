# Sprint 157 - Web Mission Export Verification Details

## Goal

Make mission export package integrity easier to diagnose from the mission page.

## Scope

- Expose checked, missing, mismatched, and unexpected file counts on mission export links.
- Show issue details on the mission page when package verification is not clean.
- Keep the existing ZIP verification logic as the single source of truth.
- Update tests and product documentation.

## Out Of Scope

- No scanner execution.
- No package mutation.
- No report regeneration.
- No browser scan launch controls.
- No customer network activity.

## Acceptance Criteria

- Valid mission packages show checked file counts in the web view.
- Corrupt or incomplete packages expose missing, mismatched, or unexpected member details.
- Mission page template includes the integrity detail block.
- The verification remains read-only and manifest-based.
