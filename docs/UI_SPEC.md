# User Interface Specification

## UI Strategy

The graphical interface should be a local web UI served by the appliance.

Recommended V2 stack:
- FastAPI backend
- server-rendered templates with Jinja2
- HTMX for simple dynamic interactions
- SQLite persistence
- Bootstrap or a small custom CSS system

React can be introduced later only if the workflow becomes complex enough to
justify it.

## Design Goals

- fast to load on a local VM
- clear for technicians
- calm and professional for customer-facing reviews
- impossible to launch scans without approved scope
- easy to export reports
- friendly to non-security users without hiding technical detail

## Navigation

Primary navigation:
- Dashboard
- Clients
- Missions
- Findings
- Reports
- Settings

Secondary mission navigation:
- Overview
- Scope
- Authorization
- Checks
- Runs
- Findings
- Reports
- Counter-tests

## Screen 1 - Dashboard

Purpose:
- show recent missions
- show missions needing review
- show critical/high findings
- show pending counter-tests

Main widgets:
- active missions
- findings by severity
- reports generated
- remediation pending

Actions:
- create client
- create mission
- open recent mission

## Screen 2 - Clients

Purpose:
- manage customer records

Fields:
- customer name
- internal reference
- technical contact
- decision contact
- contract type
- notes

Actions:
- create client
- edit client
- open missions

## Screen 3 - Mission Creation Wizard

Purpose:
- guide the technician through safe setup
- make audit creation understandable without reading the rest of the interface
- reduce the first-use cognitive load for MEDIA technicians and customer pilots

Steps:
1. Client
2. Mission details
3. Authorization
4. Scope
5. Audit type
6. Review

Required behavior:
- show only one setup step as the primary focus at a time
- provide clear Previous and Next buttons between steps
- keep a compact progress indicator visible
- validate required fields before moving to the next step
- explain missing authorization, missing scope, and missing checks in plain
  operational language
- keep selected client, audit type, targets, services, and authorization status
  visible in a compact side summary
- keep final creation disabled until the Review step confirms authorization,
  approved scope, and selected checks

The final Review step must clearly show:
- authorized scope
- excluded scope
- selected checks
- audit window
- safe-mode status

## Screen 4 - Scope Management

Purpose:
- define what can and cannot be tested

Supported item types:
- CIDR
- IP
- Hostname
- Domain
- URL

Required controls:
- add scope item
- mark as approved
- mark as excluded
- import from CSV later
- validate syntax

Guardrail:
- scan buttons remain disabled until at least one approved scope item exists.

## Screen 5 - Checks

Purpose:
- choose non-destructive checks for the mission

Check groups:
- network exposure
- TLS
- DNS/mail
- HTTP headers
- SMB
- LDAP/AD later
- MSP modules later

Each check must show:
- purpose
- target type
- expected duration estimate
- safety level
- required tool

## Screen 6 - Run Monitor

Purpose:
- follow scanner execution

Displays:
- run status
- current check
- started time
- elapsed time
- safe command preview when relevant
- logs
- findings discovered

Controls:
- start run
- stop run
- download logs

## Screen 7 - Findings Review

Purpose:
- validate findings before reporting

Columns:
- severity
- title
- asset
- category
- confidence
- status
- source

Filters:
- severity
- category
- status
- asset
- source

Actions:
- confirm
- mark false positive
- accept risk
- mark remediated
- open detail

## Screen 8 - Finding Detail

Purpose:
- provide remediation-ready detail

Sections:
- summary
- affected asset
- evidence
- risk
- remediation
- counter-test
- source modules
- status history
- technician notes

## Screen 9 - Report Generation

Purpose:
- generate deliverables

Report options:
- executive report
- technical report
- remediation plan
- counter-test report

Formats:
- HTML
- JSON
- Markdown
- PDF later

Before generation:
- warn if unreviewed high or critical findings exist
- allow excluding false positives
- allow including accepted risks

## Screen 10 - Settings

Purpose:
- configure the local appliance

Settings:
- organization name
- logo later
- report footer
- default safe mode
- paths for external tools
- update channel later
- backup/export

## UI Guardrails

- scan actions are disabled without approved scope
- destructive options do not exist in the UI
- every run shows the mission and scope
- every report shows the authorization reference
- false positive decisions require a note
- accepted risks require a note
