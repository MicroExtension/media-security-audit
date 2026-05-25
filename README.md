# MEDIA Security Audit Platform

Internal security audit platform for MSP maintenance clients.

This project is designed to support authorized, non-destructive audits:
- internal network exposure review
- external perimeter review
- DNS, mail, TLS, HTTP and service hygiene checks
- normalized findings
- remediation-focused reporting
- counter-test workflows

It is not designed for offensive automation, exploitation, brute force, payload
deployment, or post-exploitation activity.

## Current Status

Sprint 1 foundation started.

Implemented so far:
- domain models for clients, missions, scope items, assets, findings, and reports
- finding deduplication engine
- JSON, Markdown, and HTML report renderers
- safe sample data
- bootstrap CLI with a Typer-compatible fallback
- unit tests using safe fixture data only
- richer reports with executive summary, risk score, scope summary, and remediation plan
- first local web interface for dashboard, mission setup, review, and reports
- web client detail page for multi-client review
- Docker Compose deployment foundation for local Debian/Ubuntu VMs
- first web workflow forms for clients, missions, and scope
- first web finding review workflow
- web report generation for JSON, Markdown, and HTML exports
- reports include finding disposition counts and review notes
- mission pages show finding disposition counts before report generation
- web mission readiness checks and safe scan plan previews
- web mission setup updates for authorization and notes
- web scope review updates for approved and excluded targets
- web manual finding entry for structured technician observations
- web manual finding edits with scanner finding protection
- web counter-test plan for actionable findings
- web counter-test plan can record pass/fail review decisions with notes
- mission counter-test plan shows ready, passed, and failed summaries
- dashboard and client pages show counter-test ready, passed, and failed summaries
- dashboard and client mission tables show per-mission counter-test counts
- dashboard and client pages show failed counter-test mission watchlists
- failed counter-tests drive dashboard, client, and mission next-action links
- finding review requires notes for false positives, accepted risks, and counter-test results
- web mission activity log for traceability
- web check selection for mission planning
- web system status page for appliance readiness
- web run monitor for CLI scan execution history
- web mission export package for audit handoff
- structured authorization details for mission records and reports
- web authorization brief export for pre-audit approval review
- web workspace backup package for appliance operations
- web workspace inventory and integrity diagnostics
- remediation library foundation for common MSP findings
- remediation library suggestions on mission findings
- remediation library exports for technician handoff
- audit template library for repeatable MSP mission planning
- template-assisted mission creation with recommended check selection
- mission template guidance for scope, authorization, and deliverables
- template guidance in authorization briefs
- enriched mission export manifest for audit handoff
- SHA-256 checksums in mission export manifests
- mission export integrity verification in the web UI
- workspace activity log page with JSON, Markdown, HTML, and CSV exports
- activity log search and action filters with filtered exports
- activity log client and mission filters with filtered exports
- activity log date range filters with filtered exports
- activity log CSV export for spreadsheet review
- client detail pages show recent client activity and filtered Activity links
- client detail pages show finding disposition counts
- client detail pages show mission preparation status summaries
- dashboard shows workspace mission preparation status summaries
- dashboard shows workspace finding disposition counts
- dashboard shows shortcut links to operational sections
- dashboard shows client priority summary counts
- dashboard shows client risk level summary counts
- dashboard shows ready missions watchlist
- dashboard shows review missions watchlist
- dashboard shows blocked missions watchlist
- dashboard shows no-mission clients watchlist
- dashboard shows blocked clients watchlist
- dashboard shows top risk clients watchlist
- dashboard shortcut links show operational section counts
- dashboard watchlists link next actions to mission sections
- dashboard mission rows link preparation actions to mission sections
- client pages link preparation actions to mission sections
- mission pages show shortcut links to workflow sections
- client pages show shortcut links to client workflow sections
- mission pages expose client and filtered activity context links
- activity log rows link back to their client and mission context
- activity log pages summarize active filters with context links
- activity log pages expose shortcuts for filters, events, and exports
- remediation library pages expose shortcuts for filters, entries, and exports
- audit template pages expose shortcuts for filters and templates
- system status pages expose shortcuts for auth, storage, inventory, backup, and tools
- top navigation marks the active workspace area
- shared layout exposes a keyboard skip link to main content
- shared web styles expose visible keyboard focus states
- shared layout exposes accessible navigation, alert, and footer landmarks
- web tables expose screen-reader captions on operational pages
- in-page shortcut targets keep scroll spacing and visible target context
- web forms expose accessible names across operational pages
- grouped checkbox controls expose explicit form legends
- required form fields show consistent visual indicators
- healthcheck reports persistent storage readiness for deployments
- CLI preflight reports local deployment readiness without running scans
- CLI preflight supports JSON output for automation
- CLI preflight JSON output includes a schema version and status summary
- CLI preflight items include remediation actions for install technicians
- CLI preflight strict mode can fail automation on warnings
- Debian VM env helper creates local-only authenticated `.env` files
- Debian VM password rotation helper backs up `.env` and keeps authentication enabled
- Debian VM security review helper checks auth, bind, permissions, and Compose
- Debian VM firewall plan helper prints LAN access rules without applying them
- Debian VM handoff report helper summarizes safe readiness and bundle inventory checks
- Debian VM handoff bundle helper packages the handoff report only with a sidecar manifest
- Debian VM maintenance report helper aggregates safe pre-maintenance checks with backup, bundle, offline package, offline preview inventory, offline preview status, and apply checklist readiness
- Debian VM maintenance bundle helper packages the maintenance report only with a sidecar manifest
- Debian VM bundle manifest verification helper checks handoff, maintenance, and support bundle integrity
- Debian VM bundle inventory helper lists handoff, maintenance, and support bundle manifest status
- Debian VM preflight helper checks Compose readiness before service startup
- Debian VM start helper runs strict preflight before service startup
- Debian VM status helper reports Compose and preflight state without logs
- Debian VM stop helper requires confirmation and preserves data
- Debian VM restart helper stops safely, preflights, and starts again
- Debian VM backup helper archives persistent folders before updates
- Debian VM backup inventory helper lists archives and manifest status
- Debian VM backup verification helper validates archives without extraction
- Debian VM backup manifest helper writes sidecar SHA-256 metadata
- Debian VM backup manifest verification helper checks sidecar integrity
- Debian VM restore preview helper extracts backups away from live data
- Debian VM diagnostics helper records bundle, offline package, and offline preview inventory checks without app logs
- Debian VM support bundle helper packages diagnostics only with a sidecar manifest
- Debian VM update plan helper checks readiness without applying updates
- Debian VM offline update package helper creates source-only packages with manifests
- Debian VM offline update package verification helper checks sidecar integrity
- Debian VM offline update package inventory helper lists package manifest status
- Debian VM offline update preview helper extracts packages away from live code
- Debian VM offline update preview helper writes local preview manifests
- Debian VM offline update preview verification helper checks local preview manifests
- Debian VM offline update preview inventory helper lists preview manifest status
- Debian VM offline update plan helper checks package and preview readiness without applying updates
- Debian VM offline update apply checklist helper records final read-only prerequisites
- Debian VM update helper backs up, verifies a manifest, pulls, preflights, and restarts safely
- dashboard shows review backlog clients watchlist
- dashboard client list shows per-client preparation counts
- dashboard client list shows per-client finding review counts
- dashboard client list shows per-client risk summaries
- dashboard client list shows client preparation priority and next action
- dashboard client list is ordered by preparation priority and risk
- mission tables show preparation status and next action
- mission tables show compact finding review counts
- mission readiness cards link directly to the setup sections that need action

The first implementation target remains a CLI-driven V1 with a local web
interface that can set up the mission workflow:

```powershell
media-audit init --client "Client X"
media-audit scope add-domain client.example
media-audit scope add-cidr 192.168.1.0/24
media-audit run external --safe
media-audit report generate --format html,json
```

Current local bootstrap command:

```powershell
$env:PYTHONPATH='app'
python -m media_security_audit.cli sample-report --output reports\sample
```

In this Codex workspace, use the bundled Python runtime if `python` is not in
PATH.

Current local V1 workflow:

```powershell
$env:PYTHONPATH='app'

python -m media_security_audit.cli client create --name "Client X" --reference "CLIENT-001"
python -m media_security_audit.cli mission create --client-id "client_xxxxx" --name "Audit externe" --audit-type external --authorization-reference "AUTH-001"
python -m media_security_audit.cli scope add --mission-id "mission_xxxxx" --type domain --value client.example --environment external --approved
python -m media_security_audit.cli scope list --mission-id "mission_xxxxx"
python -m media_security_audit.cli finding add-sample --mission-id "mission_xxxxx"
python -m media_security_audit.cli mission show --mission-id "mission_xxxxx"
python -m media_security_audit.cli scan nmap-plan --mission-id "mission_xxxxx"
python -m media_security_audit.cli scan http-plan --mission-id "mission_xxxxx"
python -m media_security_audit.cli scan dns-plan --mission-id "mission_xxxxx" --dkim-selector default
python -m media_security_audit.cli report generate --mission-id "mission_xxxxx"
python -m media_security_audit.cli web --data-dir data --reports-dir reports --host 127.0.0.1 --port 8080
```

The `scan nmap-plan` command only prints the planned safe command. It does not
execute Nmap.

Nmap execution is guarded and requires an explicit flag:

```powershell
python -m media_security_audit.cli scan nmap-run --mission-id "mission_xxxxx" --execute
```

Execution is blocked unless the mission has an authorization reference and at
least one approved Nmap-compatible scope item.

HTTP header auditing uses approved URL scope items only:

```powershell
python -m media_security_audit.cli scope add --mission-id "mission_xxxxx" --type url --value "https://client.example" --environment external --approved
python -m media_security_audit.cli scan http-plan --mission-id "mission_xxxxx"
python -m media_security_audit.cli scan http-run --mission-id "mission_xxxxx" --execute
```

Like Nmap execution, `http-run` is blocked unless `--execute` is present.

DNS/Mail auditing uses approved domain scope items only:

```powershell
python -m media_security_audit.cli scope add --mission-id "mission_xxxxx" --type domain --value "client.example" --environment external --approved
python -m media_security_audit.cli scan dns-plan --mission-id "mission_xxxxx" --dkim-selector default
python -m media_security_audit.cli scan dns-run --mission-id "mission_xxxxx" --dkim-selector default --execute
```

`dns-run` checks SPF and DMARC by default. DKIM checks are performed only for
selectors explicitly provided with `--dkim-selector`.

Local web interface:

```powershell
$env:PYTHONPATH='app'
python -m media_security_audit.cli web --data-dir data --reports-dir reports --host 127.0.0.1 --port 8080
```

When the project is installed in a Python environment, the equivalent command
is:

```powershell
python -m pip install -e .
media-audit web --data-dir data --reports-dir reports --host 127.0.0.1 --port 8080
```

Then open:

```text
http://127.0.0.1:8080
```

The current web interface can create clients, missions, and scope items, review
findings, add manual findings, update mission setup details, review scope
approval, edit manual findings, generate stored reports, and preview safe scan
plans. It also shows a counter-test plan for actionable findings, summarizes
ready/passed/failed counter-test status, and lets a technician record pass/fail
review decisions with notes. Scan
execution remains in guarded CLI commands only while the browser workflow is
being designed. Mission pages include an activity log for web workflow
traceability and check selection for scan plan previews. The System page shows
local storage, authentication, and external tool availability without running
scanner commands. The mission Run Monitor shows recorded CLI scan runs without
adding browser scan execution. Mission export packages can be generated as ZIP
files for controlled audit handoff. Mission setup stores authorization contact,
dates, emergency contact, report recipients, and evidence retention metadata.
Mission pages can generate Markdown and HTML authorization briefs to review
approval and scope before guarded CLI execution. The System page can generate a
workspace backup ZIP containing local data and generated reports. The System
page also shows workspace inventory counts and read-only integrity diagnostics.
The Remediations page exposes a first built-in remediation library for common
HTTP, DNS/Mail, SMB, TLS, and network findings. Mission finding cards show
matching library suggestions based on finding category. The filtered
remediation library can be exported from the web UI as JSON, Markdown, or HTML.
The Templates page exposes repeatable MSP audit profiles for external,
internal, web/mail, and counter-test workflows. New missions can be created
from these templates to set the initial audit type and recommended checks.
Mission pages show selected template guidance during preparation.
Authorization briefs include selected template guidance for pre-audit review.
Mission export ZIP packages include an enriched manifest for handoff review and
archival. The manifest includes SHA-256 checksums for packaged files, and the
mission page verifies export integrity before showing the package status.
The Activity page provides a workspace-level event log for operational review
and export. The log can be filtered by search text, event action, client, and
mission, plus an inclusive date range.
Client detail pages show recent activity for the client and link directly to
the filtered Activity page.
They also show mission preparation status, including missing authorization,
approved scope, check selection, and findings awaiting review.
The dashboard shows the same preparation status across the whole workspace so
blocked missions are visible immediately.
The client list includes per-client preparation counts to identify which
customer accounts need attention first.
It also shows the highest priority action for each client, with a mission link
when the action belongs to an existing mission.
Clients are ordered by preparation priority so blocked accounts appear first.
Mission tables show the same preparation status and next action for each
mission row.
Mission readiness cards link directly to the relevant setup, scope, check
selection, findings, or report section when technician action is required.
Finding review requires a technician note before marking an item as a false
positive, accepted risk, or counter-test result.
Reports include finding disposition counts and review notes so accepted risks
and false positives remain explainable in audit exports.
Mission pages show the same disposition counts before report generation, so a
technician can spot unreviewed or accepted items quickly.
The dashboard also shows workspace-wide disposition counts to identify review
backlog without opening each mission.
Client detail pages show the same disposition counts scoped to one customer.
The dashboard and client detail pages also summarize counter-tests that are
ready, passed, or failed so retest workload is visible before opening a
mission.
Mission tables include compact review counts for new findings, accepted risks,
and false positives.
Mission tables also include compact counter-test counts for ready, passed, and
failed retests.
Failed counter-test mission watchlists link directly to the mission
counter-test plan so remediation follow-up is easier to prioritize.
When a failed counter-test exists, mission, dashboard, and client next actions
also point directly to the counter-test section.
The dashboard client list also shows compact review counts per customer, so MSP
technicians can see which client has new, accepted, or false-positive findings.
It also shows each client's risk score, active finding count, and active
high/critical count for faster prioritization.
The dashboard includes client priority summary counts, so the team can see how
many customers are blocked, ready, awaiting review, or still without a mission.
It also includes client risk level summary counts for portfolio-level risk
review.
The dashboard also highlights top-risk clients with their next action.
It also highlights clients with new findings still waiting for review.
Blocked clients are highlighted with the next preparation action before scan
execution.
Clients without any mission are also surfaced for onboarding.
Ready missions are surfaced so technicians can identify authorized work quickly.
Review missions are surfaced so near-ready work can be finished before execution.
Blocked missions are surfaced with the exact preparation action needed.
Dashboard shortcuts link directly to the main operational sections.

## Deployment

Recommended hosting model:

```text
Private GitHub repository -> local customer VM -> Docker Compose -> local web UI
```

Do not host the application as a public SaaS service for V1. Deploy it on a
local Debian/Ubuntu VM in the customer or audit environment.

Local Docker launch:

```bash
bash scripts/debian-vm-init-env.sh
bash scripts/debian-vm-start.sh
```

Local deployment preflight:

```bash
media-audit preflight --data-dir data --reports-dir reports
media-audit preflight --data-dir data --reports-dir reports --format json
media-audit preflight --data-dir data --reports-dir reports --strict
bash scripts/debian-vm-init-env.sh
bash scripts/debian-vm-rotate-password.sh --confirm
bash scripts/debian-vm-security-review.sh
bash scripts/debian-vm-firewall-plan.sh --admin-cidr 192.0.2.0/24
bash scripts/debian-vm-handoff-report.sh
bash scripts/debian-vm-handoff-bundle.sh
bash scripts/debian-vm-maintenance-report.sh
bash scripts/debian-vm-maintenance-bundle.sh
bash scripts/debian-vm-verify-bundle-manifest.sh reports/maintenance/media-audit-maintenance-YYYYMMDDTHHMMSSZ.tgz
bash scripts/debian-vm-bundle-inventory.sh --verify-manifests
bash scripts/debian-vm-preflight.sh
bash scripts/debian-vm-start.sh
bash scripts/debian-vm-status.sh
bash scripts/debian-vm-stop.sh --confirm
bash scripts/debian-vm-restart.sh --confirm
bash scripts/debian-vm-backup.sh
bash scripts/debian-vm-backup-inventory.sh --verify-manifests
bash scripts/debian-vm-verify-backup.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
bash scripts/debian-vm-backup-manifest.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
bash scripts/debian-vm-verify-backup-manifest.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
bash scripts/debian-vm-restore-preview.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
bash scripts/debian-vm-diagnostics.sh
bash scripts/debian-vm-support-bundle.sh
bash scripts/debian-vm-update-plan.sh
bash scripts/debian-vm-offline-update-package.sh
bash scripts/debian-vm-verify-offline-update-package.sh media-audit-offline-update-YYYYMMDDTHHMMSSZ.tgz
bash scripts/debian-vm-offline-update-inventory.sh --verify-manifests
bash scripts/debian-vm-offline-update-preview.sh media-audit-offline-update-YYYYMMDDTHHMMSSZ.tgz
bash scripts/debian-vm-verify-offline-update-preview.sh reports/offline-update-previews/<preview-folder>
bash scripts/debian-vm-offline-update-preview-inventory.sh --verify-manifests
bash scripts/debian-vm-offline-update-plan.sh --package media-audit-offline-update-YYYYMMDDTHHMMSSZ.tgz --preview reports/offline-update-previews/<preview-folder>
bash scripts/debian-vm-offline-update-apply-checklist.sh --package media-audit-offline-update-YYYYMMDDTHHMMSSZ.tgz --preview reports/offline-update-previews/<preview-folder>
bash scripts/debian-vm-update.sh
```

Default URL:

```text
http://127.0.0.1:8080
```

For LAN access from another workstation, set `MEDIA_AUDIT_BIND=0.0.0.0` in
`.env` and restrict access with the VM firewall or VPN.

Docker deployments require `MEDIA_AUDIT_WEB_PASSWORD` in `.env` before startup.
Use a generated password and keep `MEDIA_AUDIT_REQUIRE_AUTH=true` for customer
VMs.

Reviewed mission reports can be generated from the web UI and are written to
the configured reports directory.

Detailed instructions are in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Repository Map

```text
media-security-audit/
├── AGENTS.md
├── README.md
├── PRODUCT_SPEC.md
├── ROADMAP.md
├── ARCHITECTURE.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── app/
├── docs/
├── scripts/
├── templates/
├── tests/
└── tickets/
```

## V1 Modules

- mission and scope management
- safe Nmap scan wrapper later
- Nmap XML parser later
- HTTP security headers audit later
- DNS and mail audit later
- TLS audit adapter later
- basic SMB audit adapter later
- findings engine started
- JSON, Markdown, and HTML reports

## Local Verification

Run the current tests with:

```powershell
$env:PYTHONPATH='app'
python -m unittest discover -s tests
```

## V2 Graphical Interface

The graphical interface will be a local web UI served by the appliance.

Planned screens:
- dashboard started
- client detail page started
- clients started
- mission creation started
- scope management started
- check selection started
- run monitor started
- findings review started
- report generation started
- report finding disposition summary started
- mission finding disposition summary started
- mission export package started
- authorization tracking details started
- authorization brief export started
- workspace backup export started
- workspace inventory diagnostics started
- remediation library started
- remediation suggestions on findings started
- remediation library export started
- audit template library started
- template-assisted mission creation started
- mission template guidance started
- template guidance in authorization briefs started
- enriched mission export manifest started
- mission export checksum manifest started
- mission export integrity verification started
- workspace activity log export started
- activity log filters started
- activity log client and mission filters started
- activity log date filters started
- activity log CSV export started
- client activity summary started
- client finding disposition summary started
- client mission preparation summary started
- dashboard mission preparation summary started
- dashboard finding disposition summary started
- dashboard client preparation counts started
- dashboard client priority actions started
- dashboard client priority and risk ordering started
- mission preparation columns started
- mission row review count badges started
- mission readiness action links started
- finding review note guardrails cover false positives, accepted risks, and counter-test results
- counter-test pass/fail review actions started
- counter-test ready/passed/failed summaries started
- dashboard and client counter-test summaries started
- mission table counter-test count badges started
- failed counter-test mission watchlists started
- failed counter-test next-action routing started
- system status started
- settings

The GUI will use the same internal engine as the CLI. It must never allow scans
without an approved mission scope.

## V3 Appliance Deployment

The deployment target is a local VM appliance:
- Debian or Ubuntu Server
- Docker Compose
- local web UI on port 8080
- local database
- persistent evidence and report folders
- VMware OVA and Hyper-V VHDX packaging later

## Guardrails

- Written authorization required.
- Scope required before any scan.
- Web UI is local by default.
- Docker Web UI requires authentication by default.
- No destructive tests.
- No brute force.
- No exploitation automation.
- No exfiltration.
- Evidence must be minimal and relevant.

## First Codex Prompt

Use this prompt after creating or opening the repository:

```text
Read AGENTS.md, ROADMAP.md, and ARCHITECTURE.md.

Implement Sprint 1 only.

Goal:
Create the CLI-first V1 foundation for MEDIA Security Audit Platform.

Required:
- typed Python package
- Typer CLI
- Pydantic models for Client, Mission, ScopeItem, Asset, Finding
- findings engine with deduplication
- JSON export
- minimal Markdown and HTML report generation
- unit tests for models, finding deduplication, and report rendering

Constraints:
- no live scanning in Sprint 1
- no offensive capability
- no brute force
- no automatic exploitation
- simple architecture
- tests must run locally
```
