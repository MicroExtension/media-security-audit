# Sprint 249 - Detail Workspace UX

## Goal

Make client and mission detail pages open as clear operator workspaces instead
of dense technical records.

## Scope

- Add operator-style hero summaries to the client detail page.
- Add client mission search to the client detail page.
- Add operator-style hero summary and French primary actions to the mission page.
- Keep existing anchors, forms, reports, activity links, and scan guardrails intact.

## Safety

- No scanner changes.
- No new live network behavior.
- No credential, brute-force, exploitation, or payload workflow.
- Browser-side filtering only hides already-rendered mission rows.

## Acceptance Criteria

- Client detail gives immediate context, exports, activity, and audit creation routes.
- Mission detail gives immediate risk, findings, scope, console, session, client, and report routes.
- Existing tests still cover shortcut anchors and operator workflow hooks.
- New template hooks are covered by unit tests.
