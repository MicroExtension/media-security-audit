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

Status: required before real audits.

Owner action later:
- provide the wording used in customer authorization documents
- define the emergency contact process
- define evidence retention duration
- define who receives final reports

Codex action:
- add authorization tracking fields
- add report references to authorization id
- block scans when authorization is missing where required

## Step 5 - Choose Deployment Priority

Status: not blocking until the local UI exists.

Recommended order:
1. Docker Compose on Debian/Ubuntu
2. Hyper-V VHDX
3. VMware OVA

Owner action later:
- confirm whether Hyper-V or VMware matters most for first customer deployments
- confirm whether client appliances can have internet access for updates

Codex action:
- prepare Dockerfile and docker-compose.yml after the web UI foundation
- document offline update process later

## Step 6 - Build The GUI

Status: planned after V1 CLI foundation.

The GUI should run locally on the appliance:

```text
http://IP-VM:8080
```

Owner action:
- no action required yet
- later, validate screens and workflow wording

Codex action:
- build FastAPI/Jinja2/HTMX interface
- keep CLI and GUI on the same domain engine
- prevent scans without approved scope

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
