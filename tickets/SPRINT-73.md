# Sprint 73 - Client Page Shortcuts

## Goal

Add shortcut links to client detail pages so technicians can jump directly to
client-specific review, preparation, activity, and mission sections.

## Scope

- Add client page shortcuts below client metrics.
- Add stable anchors for dispositions, preparation, activity, and missions.
- Show simple counts from the existing client view model.
- Update tests and documentation.

## Acceptance Criteria

- Client pages expose shortcut links to the main client workflow sections.
- Shortcuts use stable static anchors and do not require JavaScript.
- Shortcut badges use already loaded client view data.
- Tests cover shortcut anchors and badge expressions.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only navigation links.
