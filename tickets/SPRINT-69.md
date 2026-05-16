# Sprint 69 - Dashboard Section Actions

## Goal

Add direct action links from dashboard watchlists to the relevant mission
workflow section so technicians can move from summary to correction quickly.

## Scope

- Add next-action labels and links to dashboard/client preparation view models.
- Link setup issues to mission setup.
- Link scope issues to scope review.
- Link check selection issues to check selection.
- Link finding review warnings to findings.
- Link ready missions to reports.
- Link clients without missions to the new mission form.
- Update dashboard templates, tests, and documentation.

## Acceptance Criteria

- Dashboard watchlists show a visible action link beside the next-action text.
- Action links use stable in-page or mission-page anchors.
- Clients without missions link to the dashboard mission creation form.
- Tests cover generated action labels and hrefs.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only navigation links.
