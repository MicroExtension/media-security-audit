# Sprint 244 - HTTP Headers Evidence And Guidance

## Goal

Make the safe HTTP headers check more useful for a real pilot audit by improving
finding quality, client-facing remediation text, and evidence retention.

## Scope

1. Expand HTTP header findings for HSTS max-age, clear-text HTTP, permissive
   CSP, Referrer-Policy, Permissions-Policy, MIME sniffing, clickjacking, CSP
   absence, and Server disclosure.
2. Attach structured metadata to HTTP header findings for JSON follow-up.
3. Write a per-target JSON evidence file with URL, method, status, and observed
   headers.
4. Store HTTP evidence paths on the scan run.
5. Route web-launched HTTP checks to the same evidence directory as other
   guarded scans.
6. Add remediation library entries for CSP, Referrer-Policy, and
   Permissions-Policy.

## Acceptance Criteria

- HTTP headers audit still requires explicit execution confirmation.
- The scanner remains non-destructive and uses conservative request behavior.
- Each successful HTTP run records evidence paths on the scan run.
- Tests cover the new header findings and evidence payloads.
- Documentation records that HTTP headers are now ready for controlled pilot
  use.
