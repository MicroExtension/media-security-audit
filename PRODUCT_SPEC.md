# Product Specification

## Product Name

Working name: MEDIA Security Audit Platform.

## Positioning

MEDIA Security Audit Platform is a local-first security audit appliance for MSP
maintenance customers.

It helps technicians run authorized, non-destructive audits, validate findings,
generate remediation-focused reports, and run counter-tests after corrective
actions.

The product is not a red-team automation platform.

## Target Users

Primary users:
- MSP technician
- security consultant
- internal infrastructure administrator

Secondary users:
- customer decision maker
- customer technical contact
- remediation owner

## Main Jobs To Be Done

The user needs to:
- deploy the tool quickly in a customer environment
- define the authorized scope clearly
- run safe internal or external checks
- understand what is exposed
- separate real findings from noise
- generate a professional report
- plan remediation work
- prove that fixes were applied

## Product Principles

- Easy before powerful.
- Scope before scan.
- Findings before raw output.
- Remediation before alarm.
- Human validation before customer report.
- CLI and GUI must use the same internal engine.
- The appliance must work without internet after installation when possible.

## V1 Experience

V1 is CLI-first with report output.

The user can:
- create a client
- create a mission
- define scope
- generate reports from findings
- run safe scanner modules as they are introduced

## V2 Experience

V2 adds a local web interface.

The user opens a browser on the appliance and follows a guided workflow:

1. Select or create client.
2. Create audit mission.
3. Upload or confirm authorization.
4. Define authorized scope.
5. Choose audit type.
6. Review planned checks.
7. Run audit.
8. Review findings.
9. Mark false positives or accepted risks.
10. Generate reports.
11. Run counter-tests after remediation.

## V3 Experience

V3 becomes a deployable customer appliance:
- VMware OVA
- Hyper-V VHDX
- Docker Compose services
- local web UI
- local database
- update workflow
- backup and export workflow

## Core Entities

Client:
- name
- internal reference
- contacts
- maintenance contract metadata

Mission:
- client
- audit type
- authorization reference
- audit window
- status
- scope
- runs
- reports

Scope item:
- type: cidr, ip, host, domain, url
- value
- environment: internal, external, cloud, unknown
- approved
- notes

Finding:
- id
- title
- severity
- asset
- source
- proof
- risk
- remediation
- counter-test
- confidence
- status

Report:
- mission
- generated date
- report type
- included findings
- output files

## Finding Statuses

- new
- confirmed
- false_positive
- accepted_risk
- remediated
- counter_test_passed
- counter_test_failed

## Mission Statuses

- draft
- scope_defined
- authorized
- ready_to_scan
- running
- review
- report_ready
- remediation
- counter_test
- closed

## Non-Goals

V1 and V2 should not include:
- automatic exploitation
- brute force
- password spraying
- payload deployment
- post-exploitation workflow
- stealth features
- destructive performance testing

## Success Metrics

Operational success:
- a technician can create a mission in less than 5 minutes
- a basic report can be generated without editing files by hand
- every report finding has remediation and counter-test guidance

Quality success:
- low false-positive rate on default checks
- deterministic parser tests
- no scan can run outside approved scope

Business success:
- reports are understandable by decision makers
- remediation plans are directly usable by the MSP team
- recurring audits can show before/after improvement

