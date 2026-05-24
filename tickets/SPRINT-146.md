# Sprint 146 - Failed Counter-Test Watchlists

## Goal

Surface missions with failed counter-tests on dashboard and client pages.

## Scope

- Add a workspace failed counter-test mission watchlist.
- Add a client-scoped failed counter-test mission watchlist.
- Link each watchlist row directly to the mission counter-test section.
- Keep counter-test review actions on mission pages only.
- Update documentation and UI tests.

## Acceptance Criteria

- Dashboard shows missions with failed counter-tests.
- Client pages show only that client's missions with failed counter-tests.
- Watchlist rows include failed, ready, passed, and risk counts.
- Watchlist action links target `#counter-test`.
- No scanner execution, network activity, or deployment workflow is added.

## Safety

- No live scanner execution.
- No browser scan execution.
- No network activity added.
- No destructive test.
- This sprint only summarizes stored finding statuses.
