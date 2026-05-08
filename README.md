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

The first implementation target remains a CLI-only V1:

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
python -m media_security_audit.cli report generate --mission-id "mission_xxxxx"
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

## Repository Map

```text
media-security-audit/
├── AGENTS.md
├── README.md
├── PRODUCT_SPEC.md
├── ROADMAP.md
├── ARCHITECTURE.md
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
- dashboard
- clients
- mission creation wizard
- scope management
- check selection
- run monitor
- findings review
- report generation
- counter-tests
- settings

The GUI will use the same internal engine as the CLI. It must never allow scans
without an approved mission scope.

## V3 Appliance Deployment

The final deployment target is a local VM appliance:
- Debian or Ubuntu Server
- Docker Compose
- local web UI on port 8080
- local database
- persistent evidence and report folders
- VMware OVA and Hyper-V VHDX packaging later

## Guardrails

- Written authorization required.
- Scope required before any scan.
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
