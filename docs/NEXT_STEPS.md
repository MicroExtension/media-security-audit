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

python -m media_security_audit.cli finding add-sample `
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
