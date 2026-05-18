# Sprint 75 - Activity Context Links

## Goal

Make the workspace activity log easier to navigate by linking each event back
to the related client and mission pages.

## Scope

- Add client and mission URLs to activity log rows.
- Render activity log client and mission names as links in the web UI.
- Keep activity exports unchanged as plain standalone evidence files.
- Update tests and product notes.

## Acceptance Criteria

- Activity log rows expose stable client and mission URLs.
- The Activity page links each row to the related client and mission context.
- Existing activity filters and exports remain unchanged.
- Tests cover the generated URLs and template usage.

## Safety

- This sprint only changes read-only web navigation.
- No scanner execution is added.
- No network activity is added.
