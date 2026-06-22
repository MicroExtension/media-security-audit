# Sprint 238 - Product UX And CVE Catalog Direction

## Goal

Move the local web interface toward a clearer MSP audit console inspired by the
target workflow: separate pages, guided test creation, visible scan progress,
and a dedicated CVE/KEV catalog.

## Scope

1. Add a product UX target document.
2. Add a dedicated CVE / KEV catalog page.
3. Add guarded CISA KEV refresh support while preserving local catalog entries.
4. Add browser-side scan launch progress feedback.
5. Update top navigation to expose clients, audits, and the CVE catalog.
6. Keep brute force automation out of the normal safe scan path.

## Acceptance Criteria

- The web UI exposes a CVE Catalog navigation item.
- `/vulnerabilities` shows catalog source, counts, severity split, remediation,
  and counter-test text.
- The catalog page can refresh from the official CISA KEV JSON feed.
- The catalog page can still import reviewed local JSON.
- Mission scan launch forms show progress feedback while a test is submitted.
- The UX target document records the page model and credential-check guardrails.
- Tests cover the new catalog parsing, view model, routes, template, styles, and
  progress UI markers.

## Safety

- No exploit automation is added.
- No unrestricted brute force is added.
- CVE matches remain candidate findings until technician validation.
- CISA KEV refresh only imports advisory metadata.
