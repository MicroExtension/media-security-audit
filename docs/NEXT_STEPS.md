# Next Steps For The Product Owner

This document explains what the product owner should do, step by step, while
Codex continues the implementation work.

## Step 1 - Keep GitHub As The Source Of Truth

Status: done.

The repository is hosted at:

```text
https://github.com/MicroExtension/media-security-audit.git
```

Owner action:
- keep the repository private
- do not add a public license yet
- invite collaborators only when needed

Codex action:
- continue development on `codex/*` branches
- push working branches to GitHub
- keep `main` stable

## Step 2 - Validate The V1 CLI Workflow

Status: in progress.

The V1 CLI workflow is:

```powershell
$env:PYTHONPATH='app'

python -m media_security_audit.cli client create `
  --name "Client X" `
  --reference "CLIENT-001"

python -m media_security_audit.cli mission create `
  --client-id "client_xxxxx" `
  --name "Audit externe Mai 2026" `
  --audit-type external `
  --authorization-reference "AUTH-001"

python -m media_security_audit.cli scope add `
  --mission-id "mission_xxxxx" `
  --type domain `
  --value client.example `
  --environment external `
  --approved

python -m media_security_audit.cli scope list `
  --mission-id "mission_xxxxx"

python -m media_security_audit.cli finding add-sample `
  --mission-id "mission_xxxxx"

python -m media_security_audit.cli mission show `
  --mission-id "mission_xxxxx"

python -m media_security_audit.cli scan nmap-plan `
  --mission-id "mission_xxxxx"

python -m media_security_audit.cli scan http-plan `
  --mission-id "mission_xxxxx"

python -m media_security_audit.cli scan dns-plan `
  --mission-id "mission_xxxxx" `
  --dkim-selector default

python -m media_security_audit.cli report generate `
  --mission-id "mission_xxxxx"
```

Owner action:
- no action required yet
- later, test these commands on a clean workstation or VM

Codex action:
- add scanner adapters only after this workflow is stable
- add better error messages
- keep report generation connected to stored findings
- improve report quality before adding live scanner modules

## Step 2.1 - Review Report Quality

Status: in progress.

Reports should now include:
- executive summary
- simple risk score
- risk level
- approved scope summary
- severity counts
- prioritized remediation plan
- detailed findings

Owner action:
- no action required yet
- later, review the wording and decide whether reports should be in French,
  English, or both

Codex action:
- keep report output deterministic
- prepare report templates for future branding
- keep dashboard shortcuts tied to existing operational section counts
- keep dashboard action links anchored to the right mission workflow sections
- keep mission table preparation actions aligned with the same workflow anchors
- keep client preparation tables aligned with the same mission workflow anchors
- keep mission detail shortcuts aligned with stable workflow section anchors
- keep client detail shortcuts aligned with stable client workflow anchors
- keep mission context links aligned with client and activity filters
- keep activity log context links aligned with client and mission routes
- keep activity filter summaries readable and linked to their context pages
- keep activity page shortcuts aligned with filters, events, and exports
- keep remediation library shortcuts aligned with filters, entries, and exports
- keep audit template shortcuts aligned with filters and template lists
- keep system status shortcuts aligned with auth, storage, inventory, backup, and tools
- keep top navigation active states aligned with stable route groups
- keep shared accessibility helpers available across all web pages
- keep visible keyboard focus styles consistent across links, buttons, and forms
- keep shared navigation, alert, and footer landmarks accessible
- keep operational table captions aligned with their section meaning
- keep in-page shortcut targets visually clear without changing page data

## Step 2.2 - Nmap Dry-Run Planning

Status: in progress.

The Nmap module starts with dry-run planning only:
- build conservative Nmap commands as argument lists
- use approved mission scope only
- exclude URL scope items from Nmap targets
- parse Nmap XML fixtures in tests
- generate normalized findings from fixture services

Owner action:
- no action required yet
- later, approve real execution defaults before live scanning is enabled

Codex action:
- keep command execution disabled until dry-run planning and parser behavior are validated
- add fixture-based tests before any real scanner execution exists

## Step 2.3 - Nmap Guarded Execution

Status: in progress.

The guarded execution path must:
- require `--execute`
- require mission authorization
- require approved scope
- execute command arguments without a shell
- reject UDP, aggressive, or NSE-script command shapes
- parse XML output into normalized findings
- store generated findings in the mission

Owner action:
- do not run live scans on customer networks until written authorization and
  scope are confirmed
- later, validate whether the default top 100 TCP ports are acceptable for your
  customer maintenance workflow

Codex action:
- test execution with mocked runners only
- do not launch Nmap from this development environment

## Step 2.4 - HTTP Header Audit

Status: in progress.

The HTTP header module:
- uses approved URL scope items only
- supports `scan http-plan` without network requests
- requires `scan http-run --execute` before making requests
- uses conservative `HEAD` requests with `GET` fallback
- generates normalized findings for missing browser security headers
- stores findings on the mission

Owner action:
- no action required yet
- later, decide whether customer-facing report wording should be French

Codex action:
- test HTTP behavior with mocked fetchers
- do not call real customer URLs from the development environment

## Step 2.5 - DNS And Mail Authentication Audit

Status: in progress.

The DNS/Mail module:
- uses approved domain scope items only
- supports `scan dns-plan` without DNS requests
- requires `scan dns-run --execute` before live DNS queries
- checks SPF and DMARC by default
- checks DKIM only for selectors explicitly provided with `--dkim-selector`
- generates normalized findings for missing or weak SPF, DMARC, and DKIM records
- stores findings on the mission

Owner action:
- no action required yet
- later, define the common DKIM selectors used by your customers, for example
  Microsoft 365, Google Workspace, Mailinblack, or other mail gateways

Codex action:
- test DNS behavior with mocked resolvers
- avoid live DNS lookups in the development environment

## Step 3 - Decide Branding

Status: not blocking.

Owner action later:
- final product name
- company display name
- logo
- report footer
- preferred colors

Default values until decided:
- product: MEDIA Security Audit Platform
- organization: M.E.D.I.A.

Codex action:
- keep branding configurable
- avoid hardcoding visual identity too deeply

## Step 4 - Prepare The Client Authorization Template

Status: in progress; template wording is still required before real audits.

Owner action later:
- provide the wording used in customer authorization documents
- define the emergency contact process
- define evidence retention duration
- define who receives final reports

Codex action:
- add authorization tracking fields: done
- add report references to authorization id: done
- add authorization brief export for pre-audit review: done
- block scans when authorization is missing where required

Current authorization metadata fields:
- authorization reference
- authorization contact
- authorization date
- authorization expiration date
- emergency contact
- report recipients
- evidence retention duration

## Step 5 - Choose Deployment Priority

Status: started.

Recommended order:
1. Docker Compose on Debian/Ubuntu
2. Hyper-V VHDX
3. VMware OVA

Owner action later:
- confirm whether Hyper-V or VMware matters most for first customer deployments
- confirm whether client appliances can have internet access for updates

Codex action:
- prepare Dockerfile and docker-compose.yml after the web UI foundation: done
- keep deployment documentation in `docs/DEPLOYMENT.md`
- document offline update process later

Current deployment recommendation:

```text
Private GitHub repository -> Debian/Ubuntu VM -> Docker Compose -> local web UI
```

Default deployment is local-only on `127.0.0.1:8080`. LAN access requires
setting `MEDIA_AUDIT_BIND=0.0.0.0` in `.env` and restricting access with a
firewall or VPN.

Docker deployments now also require `MEDIA_AUDIT_WEB_PASSWORD` in `.env`.
Keep `MEDIA_AUDIT_REQUIRE_AUTH=true` for customer VMs.

## Step 6 - Build The GUI

Status: started.

The GUI should run locally on the appliance:

```text
http://IP-VM:8080
```

Current local development command:

```powershell
$env:PYTHONPATH='app'
python -m media_security_audit.cli web --data-dir data --reports-dir reports --host 127.0.0.1 --port 8080
```

Installed environment command:

```powershell
python -m pip install -e .
media-audit web --data-dir data --reports-dir reports --host 127.0.0.1 --port 8080
```

Owner action:
- no action required yet
- later, validate screens and workflow wording

Codex action:
- build FastAPI/Jinja2 interface incrementally
- keep scan execution out of the UI until browser execution controls are approved
- keep CLI and GUI on the same domain engine
- prevent scans without approved scope

Current GUI status:
- dashboard can show clients and missions
- client detail pages show client mission history and risk metrics
- mission pages can show scope, findings, remediation plan, and reports
- web forms can create clients, missions, and scope items
- mission setup details can be updated from mission pages
- scope items can be reviewed, corrected, approved, or excluded from mission pages
- manual findings can be added from mission pages
- manual findings can be edited from mission pages
- finding status can be reviewed from mission pages
- false positive and accepted risk statuses require a review note
- mission pages show finding disposition counts
- counter-test plans are visible from mission pages
- mission activity events are recorded and visible from mission pages
- mission authorization details are editable from mission pages
- authorization briefs can be generated from mission pages
- audit checks can be selected from mission pages for planning
- audit templates are visible from the web navigation
- new missions can use a template to set audit type and initial checks
- mission pages show selected template guidance for preparation
- authorization briefs include selected template guidance
- a first remediation library is visible from the web navigation
- mission findings show matching remediation library suggestions
- remediation library filters can be exported as JSON, Markdown, or HTML
- CLI scan runs are recorded and visible in the mission Run Monitor
- system status shows local storage, authentication, and tool availability
- workspace inventory and integrity diagnostics are visible on the System page
- workspace backups can be generated from the System page
- reviewed reports can be generated from mission pages
- reports include finding disposition counts and review notes
- mission ZIP export packages can be generated from mission pages
- mission ZIP manifests include client, template, scope, report, and evidence metadata
- mission ZIP manifests include SHA-256 checksums for packaged files
- mission pages verify mission ZIP package integrity from the manifest
- a workspace Activity page lists mission events and exports the log
- Activity log filters can narrow events by search text and action
- Activity log filters can narrow events by client and mission
- Activity log filters can narrow events by inclusive date range
- Activity log exports include CSV for spreadsheet review
- client detail pages show recent client activity and link to the filtered
  Activity page
- client detail pages show finding disposition counts
- client detail pages show mission preparation status for missing
  authorization, scope, checks, and finding review
- dashboard shows workspace mission preparation status across clients
- dashboard shows workspace finding disposition counts
- dashboard shows shortcut links to operational sections
- dashboard shows client priority summary counts
- dashboard shows client risk level summary counts
- dashboard shows ready missions for authorized work
- dashboard shows review missions close to ready
- dashboard shows blocked missions with next preparation actions
- dashboard shows clients without any mission
- dashboard shows blocked clients with next preparation actions
- dashboard shows top-risk clients with next actions
- dashboard shows clients with new findings waiting for review
- dashboard client list shows per-client preparation counts
- dashboard client list shows per-client finding review counts
- dashboard client list shows per-client risk summaries
- dashboard client list shows each client's priority and next action
- dashboard client list is ordered by preparation priority and risk
- dashboard and client mission tables show preparation status and next action
- dashboard and client mission tables show compact finding review counts
- mission readiness cards link to the setup section that needs action
- mission readiness and safe scan plan previews are visible from mission pages
- scan execution remains CLI-only

## Step 7 - Add Safe Scanner Modules

Status: after V1 foundation.

Initial module order:
1. Nmap safe adapter and XML parser
2. HTTP headers
3. DNS/Mail
4. TLS via testssl.sh
5. SMB basic checks

Owner action before real modules:
- confirm accepted Nmap timing defaults
- confirm whether UDP scans are excluded by default
- confirm customer notification process before scans

Codex action:
- implement dry-run first
- add parser fixtures
- avoid aggressive or intrusive defaults
