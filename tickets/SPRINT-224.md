# Sprint 224 - CVE/KEV Validation Cards

Status: implemented.

## Goal

Make CVE/KEV candidate matches easier to validate and safer to store from the
mission page.

## Scope

- Add technician-oriented CVE/KEV validation cards.
- Show priority, priority reason, risk, remediation, counter-test, references,
  and pre-storage validation steps for each candidate.
- Keep the detailed CVE/KEV table for technical review.
- Make candidate finding storage idempotent so repeated review clicks do not
  create duplicate CVE findings.

## Out of Scope

- Do not download vulnerability data from the internet.
- Do not add exploitation checks.
- Do not add brute force, payload, privilege escalation, or exfiltration
  features.
- Do not bypass human validation before customer communication.

## Acceptance Criteria

- Mission pages show a readable validation card for each CVE/KEV candidate.
- Known exploited candidates are prioritized for review.
- Repeated candidate storage actions skip already stored candidates.
- Existing tests continue to pass.
