# Sprint 247 - Session Cockpit UX

## Goal

Make the post-wizard audit experience easier to follow before continuing scanner
service development.

## Scope

- Translate the audit console and session dashboard toward a French technician
  workflow.
- Present the mission as a cockpit with preparation, launch, analysis, and
  delivery phases.
- Add a visual phase lane to the session dashboard.
- Keep scan execution, authorization, and report generation behavior unchanged.

## Acceptance Criteria

- The console exposes clear preparation, launch, analysis, and delivery phases.
- The session dashboard shows progress, services, targets, executions, findings,
  CVE/KEV review, and remediation follow-up in separated sections.
- The interface remains consistent with the dark operator shell.
- No live scan behavior, exploitation, or brute-force behavior is added.

## Safety

This sprint is UI and workflow guidance only. Guarded scanner execution remains
controlled by existing authorization, approved scope, and explicit execution
checks.
