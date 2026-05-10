# Sprint 31 - Template Guidance In Authorization Briefs

Goal: Include selected audit template guidance in pre-audit authorization briefs
so the approval document captures methodology, expected scope, authorization
requirements, and deliverables.

## Scope

1. Read the selected audit template when rendering authorization briefs.
2. Add template summary, cadence, and recommended checks to Markdown and HTML
   briefs.
3. Add scope guidance, authorization requirements, and expected deliverables to
   Markdown and HTML briefs.
4. Keep missions without templates unchanged.
5. Add tests for Markdown and HTML template guidance output.

## Safety

- No scanner execution.
- No network activity.
- No mission mutation.
- Brief generation remains a local file export only.

## Acceptance Criteria

- Authorization briefs for templated missions include an Audit Template section.
- Markdown and HTML outputs include template title, scope guidance, and
  deliverables.
- Missions without templates do not show a template section.
- Tests cover the new rendering behavior.
