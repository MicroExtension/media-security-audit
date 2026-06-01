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

python -m media_security_audit.cli mission readiness `
  --mission-id "mission_xxxxx" `
  --format json

python -m media_security_audit.cli scan nmap-plan `
  --mission-id "mission_xxxxx"

python -m media_security_audit.cli scan http-plan `
  --mission-id "mission_xxxxx"

python -m media_security_audit.cli scan dns-plan `
  --mission-id "mission_xxxxx" `
  --dkim-selector default

python -m media_security_audit.cli scan plan-all `
  --mission-id "mission_xxxxx"

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
- keep form accessible names aligned with their workflow action
- keep grouped checkbox controls associated with explicit legends
- keep required form fields visibly marked in operational workflows
- keep deployment healthchecks coarse and free of sensitive customer data
- keep deployment preflight checks non-destructive and scanner-free
- keep deployment preflight JSON output stable for automation
- keep deployment preflight JSON schema versioned for install scripts
- keep deployment preflight action hints short and technician-focused
- keep deployment preflight strict mode opt-in for install gates
- keep Debian VM env initialization local-only and non-overwriting
- keep Debian VM password rotation explicit and auth-preserving
- keep Debian VM security review secret-free and scanner-free
- keep Debian VM firewall planning read-only and technician-reviewed
- keep Debian VM handoff reports log-free, customer-data-free, and bundle-aware
- keep Debian VM handoff bundles limited to handoff reports and sidecar manifests
- keep Debian VM maintenance reports log-free and restore-free
- keep Debian VM maintenance bundles limited to maintenance reports and sidecar manifests
- keep Debian VM bundle manifest verification checksum-only and restore-free
- keep Debian VM bundle inventory read-only and restore-free
- keep Debian VM service startup guarded by strict preflight
- keep Debian VM status checks log-free and scanner-free
- keep Debian VM stop helpers explicit and data-preserving
- keep Debian VM restart helpers explicit, data-preserving, and preflighted
- keep Debian VM helper scripts preflight-only and scanner-free
- keep Debian VM backup helpers local-only and update-safe
- keep Debian VM backup inventory read-only and restore-free
- keep Debian VM backup verification read-only and restore-free
- keep Debian VM backup manifests checksum-only and restore-free
- keep Debian VM backup manifest verification checksum-only and restore-free
- keep Debian VM restore previews isolated from live data folders
- keep Debian VM diagnostics free of customer file contents and app logs while recording bundle and offline package inventory status
- keep Debian VM support bundles limited to diagnostics reports and sidecar manifests
- keep Debian VM update planning read-only and maintenance-window focused
- keep Debian VM offline update planning package-verification-only until apply workflow is designed
- keep Debian VM update helpers guarded by backup, manifest verification, and strict preflight

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

## Step 2.6 - TLS testssl.sh Audit

Status: started.

The TLS module:
- uses approved HTTPS URL, domain, host, or IP scope items only
- supports `scan tls-plan` without executing `testssl.sh`
- requires `scan tls-run --execute` before running `testssl.sh`
- builds conservative commands with JSON evidence output
- parses fixture JSON into normalized TLS findings
- stores findings on the mission

Owner action:
- no action required yet
- later, confirm whether `testssl.sh` should be installed in the VM image or
  documented as a required customer appliance dependency

Codex action:
- test TLS behavior with mocked runners
- do not run `testssl.sh` from the development environment

## Step 2.7 - SMB Basic Audit

Status: started.

The SMB module:
- uses approved host, IP, or domain scope items only
- supports `scan smb-plan` without executing `smbclient`
- requires `scan smb-run --execute` before running `smbclient`
- performs anonymous listing checks only
- rejects credentialed and interactive command shapes
- parses fixture `smbclient -g` output into normalized findings
- stores findings and evidence on the mission

Owner action:
- no action required yet
- later, confirm whether anonymous SMB listing checks are acceptable by default
  for internal maintenance audits

Codex action:
- test SMB behavior with mocked runners
- do not run `smbclient` from the development environment

## Step 2.8 - LDAP Basic Audit

Status: started.

The LDAP module:
- uses approved host, IP, or domain scope items only
- supports `scan ldap-plan` without executing `ldapsearch`
- requires `scan ldap-run --execute` before running `ldapsearch`
- performs anonymous RootDSE base-scope checks only
- rejects credentialed, file-driven, extended, and subtree command shapes
- parses fixture LDIF output into normalized findings
- stores findings and evidence on the mission

Owner action:
- no action required yet
- later, confirm whether anonymous LDAP RootDSE checks are acceptable by
  default for internal maintenance audits

Codex action:
- test LDAP behavior with mocked runners
- do not run `ldapsearch` from the development environment

## Step 2.9 - Consolidated Scan Plan

Status: started.

The consolidated plan command:
- uses the mission selected checks
- reuses the same safe previews shown in the web UI
- reports ready and blocked checks together
- supports text output for technicians
- supports JSON output for automation
- supports JSON and Markdown web downloads from mission pages
- is included in mission export ZIP packages
- is embedded in authorization briefs for pre-audit approval review
- records `execution=not_executed`
- never runs scanner commands

The mission readiness command:
- reports authorization, approved scope, check selection, finding review, and
  generated report status
- includes the scan plan summary
- supports text and JSON output
- supports strict mode for install or maintenance gates
- records `execution=not_executed`
- never runs scanner commands

Mission readiness exports:
- are available from mission pages as JSON and Markdown
- are included in mission export ZIP packages
- keep the same `execution=not_executed` marker
- never run scanner commands

Owner action:
- no action required yet
- later, decide whether this plan should be attached to the customer
  authorization brief before every audit

Codex action:
- keep this command read-only
- keep CLI and web scan planning aligned
- use the JSON schema for deployment and technician automation
- keep mission export packages useful for pre-audit authorization review
- keep authorization briefs explicit about planned commands and non-execution
- keep mission readiness output aligned with the same web readiness rules
- keep mission export packages useful for handoff and readiness review

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
- keep offline update planning read-only until package application is designed
- keep offline update packages source-only and manifest-backed
- keep offline update package verification checksum-only and extraction-free
- keep offline update package inventory read-only and extraction-free
- keep offline update previews isolated from live repository and data folders
- keep offline update preview manifests local, source-focused, and non-application status only
- keep offline update preview verification read-only and package-metadata focused
- keep offline update preview inventory read-only and manifest-aware
- keep offline update planning connected to preview verification without applying packages
- keep offline update apply readiness read-only until package application is designed

Current deployment recommendation:

```text
Private GitHub repository -> Debian/Ubuntu VM -> Docker Compose -> local web UI
```

Default deployment is local-only on `127.0.0.1:8080`. LAN access requires
setting `MEDIA_AUDIT_BIND=0.0.0.0` in `.env` and restricting access with a
firewall or VPN.

Docker deployments now also require `MEDIA_AUDIT_WEB_PASSWORD` in `.env`.
Keep `MEDIA_AUDIT_REQUIRE_AUTH=true` for customer VMs.
The unauthenticated `/healthz` endpoint only reports coarse service and storage
readiness and is intended for local Docker/VM health monitoring.
Run `media-audit preflight --data-dir data --reports-dir reports` on a VM before
customer use to verify storage, web authentication settings, inventory, and
external tool availability without running scans.
Use `--format json` when the result must be consumed by an install script or
monitoring wrapper.
Use `--strict` when warnings should fail an install gate.
Use `bash scripts/debian-vm-init-env.sh` on a fresh VM to create a local-only
`.env` with authentication enabled and a generated web password.
Use `bash scripts/debian-vm-rotate-password.sh --confirm` to rotate
`MEDIA_AUDIT_WEB_PASSWORD`, back up `.env`, and keep authentication enabled.
Use `bash scripts/debian-vm-security-review.sh` before customer handoff to
check `.env` permissions, authentication, LAN binding, and Compose config
without printing secrets or collecting logs.
Use `bash scripts/debian-vm-firewall-plan.sh --admin-cidr <cidr>` before LAN
exposure to print firewall commands for technician review without applying
them.
Use `bash scripts/debian-vm-handoff-report.sh` before customer handoff to write
a local readiness report with bundle inventory under `reports/handoff` without
collecting logs or customer file contents.
Use `bash scripts/debian-vm-handoff-bundle.sh` to generate a fresh handoff
report and package only that report for handoff review. Review the generated
sidecar manifest before sharing the bundle.
Use `bash scripts/debian-vm-maintenance-report.sh` before approved maintenance
to collect security review, backup inventory, bundle inventory, offline update
package inventory, offline update preview inventory, optional offline preview
verification, optional offline apply checklist readiness, and update plan output
without starting services, extracting backups, applying packages, or collecting
logs. Set `MEDIA_AUDIT_OFFLINE_UPDATE_PACKAGE` and
`MEDIA_AUDIT_OFFLINE_UPDATE_PREVIEW` when the report should include package,
preview, and checklist verification details.
Use `bash scripts/debian-vm-maintenance-bundle.sh` to generate a fresh
maintenance report and package only that report for review. Review the
generated sidecar manifest before sharing the bundle.
Use `bash scripts/debian-vm-verify-bundle-manifest.sh <bundle.tgz>` to confirm
handoff, maintenance, or support bundle integrity after copying.
Use `bash scripts/debian-vm-bundle-inventory.sh --verify-manifests` to list
handoff, maintenance, and support bundles with manifest status without deleting
or extracting anything.
Use `bash scripts/debian-vm-preflight.sh` after `.env` is configured to validate
Docker Compose, persistent folders, image build, and strict preflight before
starting the service.
Use `bash scripts/debian-vm-start.sh` to run strict preflight and start Docker
Compose only if deployment checks pass.
Use `bash scripts/debian-vm-status.sh` for a quick log-free status check of
`.env`, Docker Compose, service state, and deployment preflight JSON.
Use `bash scripts/debian-vm-stop.sh --confirm` to stop the service without
removing containers, volumes, or persistent folders.
Use `bash scripts/debian-vm-restart.sh --confirm` after approved maintenance to
stop without removing data and start again through strict preflight.
Use `bash scripts/debian-vm-backup.sh` before customer-impacting updates to
archive `data`, `runs`, `reports`, and `evidence` without starting services or
running scanners.
Use `bash scripts/debian-vm-backup-inventory.sh --verify-manifests` to list
local backups and confirm sidecar manifest status without deleting or restoring
anything.
Use `bash scripts/debian-vm-verify-backup.sh <backup.tgz>` to confirm a backup
archive can be listed and includes all persistent folders before trusting it.
Use `bash scripts/debian-vm-backup-manifest.sh <backup.tgz>` to write a sidecar
manifest with backup size and SHA-256 metadata without extracting data.
Use `bash scripts/debian-vm-verify-backup-manifest.sh <backup.tgz>` to confirm
the sidecar manifest still matches the archive before copying or restoring.
Use `bash scripts/debian-vm-restore-preview.sh <backup.tgz>` to extract a backup
into `reports/restore-previews` for inspection without replacing live folders.
Use `bash scripts/debian-vm-diagnostics.sh` when support needs VM state; it
writes Git, Compose, folder-size, preflight, bundle inventory, offline update
package inventory, and offline update preview inventory information under
`reports/support` without application logs or customer file contents.
Use `bash scripts/debian-vm-support-bundle.sh` to generate a fresh diagnostics
report and package only that report for support review. Review the generated
sidecar manifest before sharing the bundle.
Use `bash scripts/debian-vm-update-plan.sh` before approved maintenance to
check branch, tracked changes, `.env`, and backup readiness without applying
updates.
Use `bash scripts/debian-vm-offline-update-package.sh` from a clean `main`
maintainer repository to create a source-only offline package and manifest.
Use `bash scripts/debian-vm-verify-offline-update-package.sh <package.tgz>` to
confirm the offline package manifest still matches before copying it to a
customer VM.
Use `bash scripts/debian-vm-offline-update-inventory.sh --verify-manifests` to
list local offline update packages and manifest status without extracting or
applying packages.
Use `bash scripts/debian-vm-offline-update-preview.sh <package.tgz>` to inspect
a verified package under `reports/offline-update-previews` without replacing the
live repository or data folders. The preview folder includes
`preview-manifest.txt` with package size, SHA-256, top-level source folder, and
explicit non-application status for review.
Use `bash scripts/debian-vm-verify-offline-update-preview.sh <preview-dir>` to
confirm the preview manifest still matches the source package and extracted
source folder without extracting or applying anything.
Use `bash scripts/debian-vm-offline-update-preview-inventory.sh --verify-manifests`
to list local offline update previews and verify preview manifests without
deleting, extracting, applying, or running scanners.
Use `bash scripts/debian-vm-offline-update-plan.sh --package <package.tgz> --preview <preview-dir>`
before offline maintenance to check branch, tracked changes, `.env`, backup
readiness, package metadata, and preview verification without applying or
extracting the package.
Use `bash scripts/debian-vm-offline-update-apply-checklist.sh --package <package.tgz> --preview <preview-dir>`
to record the final read-only prerequisites for a future offline application
workflow. It verifies package and preview metadata, runs the offline plan, and
still records `application=not_implemented`.
Use `bash scripts/debian-vm-update.sh` for approved updates on `main`; it backs
up first, writes and verifies a sidecar manifest, requires a clean tracked
worktree, pulls with `--ff-only`, rebuilds, runs strict preflight, then restarts
Docker Compose.

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
- false positive, accepted risk, and counter-test statuses require a review note
- mission pages show finding disposition counts
- counter-test plans are visible from mission pages
- counter-test plans show ready, passed, and failed summaries
- counter-test plan cards can record pass/fail review decisions with notes
- mission activity events are recorded and visible from mission pages
- mission authorization details are editable from mission pages
- authorization briefs can be generated from mission pages
- audit checks can be selected from mission pages for planning
- audit templates are visible from the web navigation
- new missions can use a template to set audit type and initial checks
- mission pages show selected template guidance for preparation
- authorization briefs include selected template guidance
- authorization briefs include selected scan plan summaries
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
- mission pages expose mission ZIP manifest JSON and Markdown downloads
- CLI mission export inventory lists package status for handoff review
- web mission export inventory lists package status for handoff review
- web mission export inventory downloads JSON and Markdown handoff files
- web mission export inventory filters handoff files by search text and status
- web mission export inventory downloads CSV files for spreadsheet review
- web mission export inventory summarizes active filters and page shortcuts
- web mission export inventory filters handoff files by client for MSP review
- client and dashboard pages link to each client's filtered export inventory
- local Pilot page guides first client deployment and closeout review
- local Pilot page exports a Markdown handoff summary for technician handoff
- local Pilot page exports a Markdown bundle index for extracted evidence review
- local Pilot page exports a Markdown runbook for technician handoff
- local Pilot page exports a Markdown acceptance checklist for beta sign-off
- local Pilot page summarizes workspace readiness from status, exports, and backup state
- local Pilot page exports workspace readiness as Markdown for beta evidence
- local Pilot page exports workspace readiness as JSON for automation handoff
- local Pilot page bundles pilot evidence exports as a local ZIP with a manifest
- local Pilot evidence bundle includes the attention follow-up Markdown file
- local Pilot evidence bundle includes the handoff summary Markdown file
- local Pilot evidence bundle includes the review index Markdown file
- local Pilot evidence bundle includes the readiness JSON file
- local Pilot page exports the pilot evidence manifest JSON before bundle handoff
- local Pilot evidence manifest includes readiness summary counters
- local Pilot page exports a Markdown verification sheet for pilot evidence checks
- local Pilot page shows the pilot evidence bundle file inventory before download
- local Pilot page shows readiness rollup counters before pilot handoff
- local Pilot page highlights non-ready attention items before pilot handoff
- local Pilot page exports non-ready attention items as Markdown for handoff follow-up
- CLI mission export manifest output reads ZIP manifests after handoff
- mission pages verify mission ZIP package integrity from the manifest
- CLI mission export verification checks mission ZIP integrity after handoff
- mission pages show export integrity counts and issue details
- mission pages expose export verification JSON and Markdown downloads
- mission pages expose scan plan JSON and Markdown downloads
- mission export ZIP packages include scan plan JSON and Markdown files
- a workspace Activity page lists mission events and exports the log
- Activity log filters can narrow events by search text and action
- Activity log filters can narrow events by client and mission
- Activity log filters can narrow events by inclusive date range
- Activity log exports include CSV for spreadsheet review
- client detail pages show recent client activity and link to the filtered
  Activity page
- client detail pages show finding disposition counts
- client detail pages show counter-test ready, passed, and failed summaries
- client detail pages show failed counter-test mission watchlists
- client detail pages show mission preparation status for missing
  authorization, scope, checks, and finding review
- dashboard shows workspace mission preparation status across clients
- dashboard shows workspace finding disposition counts
- dashboard shows workspace counter-test ready, passed, and failed summaries
- dashboard shows failed counter-test mission watchlists
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
- dashboard and client mission tables show compact counter-test counts
- failed counter-tests drive mission, dashboard, and client next-action links
- mission readiness cards link to the setup section that needs action
- mission readiness and safe scan plan previews are visible from mission pages
- CLI mission readiness checks are available for technician automation
- mission readiness exports are available from mission pages and mission packages
- TLS testssl.sh scan plan previews are available when the TLS check is selected
- SMB scan plan previews are available when the SMB check is selected
- LDAP scan plan previews are available when the LDAP check is selected
- scan execution remains CLI-only

## Step 7 - Add Safe Scanner Modules

Status: after V1 foundation.

Initial module order:
1. Nmap safe adapter and XML parser
2. HTTP headers
3. DNS/Mail
4. TLS via testssl.sh: started
5. SMB basic checks: started

Owner action before real modules:
- confirm accepted Nmap timing defaults
- confirm whether UDP scans are excluded by default
- confirm customer notification process before scans

Codex action:
- implement dry-run first
- add parser fixtures
- avoid aggressive or intrusive defaults
