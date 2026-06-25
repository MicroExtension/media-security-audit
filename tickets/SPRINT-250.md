# Sprint 250 - Delivery And Remediation UX

## Goal

Make export handoff and remediation guidance easier to understand before the
next scanner/service sprint.

## Scope

- Turn the Exports page into an operator delivery center.
- Highlight handoff readiness, package status, and download actions.
- Turn the Remediations page into a clear correction library.
- Add local browser-side remediation search across title, risk, remediation, and counter-test content.
- Preserve existing export filters, downloads, package verification links, and remediation exports.

## Safety

- No scanner behavior changes.
- No live network calls.
- No exploitation, brute force, payload, credential attack, or destructive workflow.
- Search only filters already-rendered remediation cards in the browser.

## Acceptance Criteria

- Exports page has a delivery-focused hero and action bar.
- Remediations page has a remediation-focused hero and local search.
- Existing export routes and downloads stay unchanged.
- Unit tests cover the new template and CSS hooks.
