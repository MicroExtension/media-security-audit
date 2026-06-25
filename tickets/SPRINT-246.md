# Sprint 246 - Guided Operator Audit UX

## Goal

Make the guided audit creation workflow easier for a MEDIA technician to use
before continuing scanner service development.

## Scope

- Keep the dark operator shell.
- Convert the wizard copy toward a French technician workflow.
- Add a compact overview explaining the audit creation path.
- Add clear internal/external mode cards.
- Keep a persistent audit summary and gated step validation.
- Preserve the existing safe execution model and console handoff.

## Acceptance Criteria

- The guided audit page reads as an operator workflow, not a dense form.
- The user can move through client, mode, targets, services, credentials, and
  validation with previous/next buttons.
- Internal and external modes are selectable with visible cards.
- Target coverage, service coverage, credential guardrails, and console handoff
  remain explicit.
- No live scan behavior, exploitation, or brute-force behavior is added.

## Safety

This sprint is UI and workflow guidance only. Scanner execution remains guarded
by existing authorization, approved scope, and explicit execution controls.
