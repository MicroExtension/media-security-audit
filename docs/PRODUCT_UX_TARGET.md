# MEDIA Security Audit UX Target

## Product Direction

MEDIA Security Audit must feel like a guided MSP audit console, not a dense
administration page. Each screen should have one job, short decisions, and clear
handoff actions.

## Target Navigation

- Overview: workspace health, urgent actions, ready audits, and recent results.
- Clients: client list, client creation, client context, missions, and history.
- Audits: mission list, status, progress, and next technician action.
- New Audit: step-by-step wizard with Previous and Next controls.
- CVE Catalog: automatic CISA KEV refresh, reviewed local imports, and catalog status.
- Remediations: readable remediation library and counter-test guidance.
- Exports: PDF, JSON, Markdown, HTML, and handoff packages.
- System: VM readiness, tools, update state, and support diagnostics.

## New Audit Wizard

The audit creation flow should stay separated into small screens:

1. Client: select or create the customer.
2. Mode: choose internal, external, or mixed.
3. Targets: add CIDR, IP, domain, URL, and AD/LDAP host entries.
4. Services: select HTTP, TLS, DNS/Mail, SMB, LDAP/AD, and Nmap inventory.
5. Guardrails: confirm authorization, scope, customer contact, and test window.
6. Review: show exactly what will be tested before the mission is created.

## Scan Execution

Live execution must show visible progress:

- authorization confirmed
- command prepared
- scan running
- evidence and findings importing
- redirect to run monitor

The progress display is not a replacement for backend job tracking. A later
sprint should move scanner execution to a job queue so progress can be updated
from stored run state instead of only browser-side feedback.

## CVE / KEV Catalog

The catalog should support:

- automatic CISA KEV refresh from the official JSON feed
- reviewed local JSON imports for internal advisories
- source, update date, severity, and known-exploited status
- correlation against detected products, versions, CPEs, and service evidence
- technician validation before candidate CVEs become findings

Future enrichment can add NVD CVSS and EPSS, but only if the source, timestamp,
and matching confidence remain visible.

## Findings And Remediations

Every finding shown to a technician or customer must include:

- plain-language explanation
- affected asset
- severity and confidence
- proof
- business risk
- remediation
- counter-test command or procedure
- status for follow-up and accepted risk tracking

Reports should highlight critical and high findings first, then group the rest
by action priority instead of raw scanner order.

## Credential Checks

Do not add unrestricted brute force automation to the product.

Allowed future direction:

- imported credential exposure list review
- password policy and lockout posture checks
- offline hash/password audit when the customer explicitly provides material
- tightly rate-limited, written-authorized credential validation as a separately
  gated module

Each credential check must be disabled by default, logged, scoped, and separated
from normal safe scans.

## Visual Direction

Use a darker operational console style only where it improves scanning and
triage. Keep the MSP product readable:

- dense but not overloaded tables
- clear status badges
- one primary action per page section
- cards only for repeated entities or focused summaries
- no long forms that mix setup, execution, findings, and exports on one screen
