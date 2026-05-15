# Sprint 67 - Dashboard Shortcuts

## Goal

Add internal dashboard shortcuts so technicians can jump directly to the main
operational sections on a long dashboard page.

## Scope

- Add shortcut links below the workspace metrics.
- Add stable anchors to key dashboard sections.
- Style the shortcuts with the existing dashboard visual language.
- Add a template regression test.
- Update documentation.

## Acceptance Criteria

- Dashboard exposes shortcuts for ready, review, and blocked missions.
- Dashboard exposes shortcuts for no-mission, blocked, top-risk, and review
  backlog clients.
- Shortcuts use static anchors and do not require JavaScript.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard navigation.
