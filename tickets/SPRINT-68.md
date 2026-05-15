# Sprint 68 - Dashboard Shortcut Counts

## Goal

Show operational counts directly inside dashboard shortcut links so technicians
can see the size of each watchlist before jumping to the section.

## Scope

- Add count badges to existing dashboard shortcuts.
- Reuse already prepared dashboard view collections.
- Style the badges with the existing dashboard visual language.
- Extend the template regression test.
- Update documentation.

## Acceptance Criteria

- Ready, review, and blocked mission shortcuts show their current counts.
- No-mission, blocked, top-risk, and review backlog client shortcuts show their
  current counts.
- Preparation shortcut shows its current item count.
- No JavaScript is required.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only dashboard display information.
