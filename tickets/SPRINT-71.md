# Sprint 71 - Client Preparation Actions

## Goal

Show direct preparation action links on client pages so technicians can move
from a client-specific preparation list to the right mission workflow section.

## Scope

- Display existing client preparation action links in `client.html`.
- Display existing mission row preparation action links in the client mission table.
- Add template and view-model assertions.
- Update documentation.

## Acceptance Criteria

- Client preparation rows expose visible action links.
- Client mission rows expose visible preparation action links.
- Links target the existing mission workflow anchors.
- Tests cover the template and generated client preparation hrefs.
- Scan execution remains CLI-only.

## Safety

- No live scanner execution is added.
- No network activity is added.
- The sprint only adds read-only navigation links.
