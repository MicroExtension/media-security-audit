# Sprint 25 - Remediation Library Foundation

## Goal

Start a built-in remediation library so technicians can quickly reuse consistent
MSP remediation wording and counter-test guidance.

## Scope

1. Add structured remediation entries for common findings.
2. Cover first HTTP headers, DNS/Mail, RDP, SMB, and TLS cases.
3. Add category and query filtering.
4. Add a local Web UI page for browsing the library.
5. Add navigation from the main web layout.
6. Add unit tests for entry structure, filtering, and web view construction.

## Safety Constraints

- The library is informational only.
- No scan execution is added.
- No automatic finding mutation is added.
- No external lookups or live validation are performed.

## Acceptance Criteria

- The Remediations page lists built-in entries.
- Each entry includes risk, remediation, and counter-test text.
- Filtering by category and search query works.
- Tests cover the built-in library without network activity.
