# Architecture

## Product Shape

MEDIA Security Audit Platform is a local-first audit tool.

The platform has three layers:

1. Domain layer
   - clients
   - missions
   - scope
   - assets
   - findings
   - reports

2. Scanner adapters
   - Nmap
   - testssl.sh
   - DNS and mail checks
   - HTTP headers
   - SMB/LDAP safe checks

3. Presentation layer
   - CLI
   - local web UI
   - Markdown report
   - HTML report
   - JSON export

## Data Flow

```text
Mission + Scope
      |
      v
Scope Validator
      |
      v
Scanner Adapter
      |
      v
Raw Evidence
      |
      v
Parser / Normalizer
      |
      v
Finding Engine
      |
      v
Reports + Counter-Test Plan
```

## Scanner Adapter Rules

Adapters must:
- accept validated scope only
- expose a dry-run mode when possible
- return structured execution metadata
- capture stdout, stderr, exit code, and command arguments
- avoid shell interpolation
- avoid aggressive timing by default

Adapters must not:
- run exploit modules
- guess credentials
- brute force services
- bypass authentication
- mutate client systems

## Finding Engine

The finding engine is the stable center of the product.

Responsibilities:
- normalize findings from scanner adapters
- deduplicate findings
- assign severity
- attach remediation text
- attach counter-test procedures
- export stable JSON

The engine must support multiple sources for the same finding.

## Persistence

V1 can start file-based:
- `data/clients/*.json`
- `data/missions/*.json`
- `runs/<mission-id>/evidence/`
- `runs/<mission-id>/reports/`

SQLite can be introduced once workflows stabilize.

## CLI Shape

Target command family:

```powershell
media-audit init --client "Client X"
media-audit mission create --client-id client-x --name "External audit May 2026"
media-audit scope add-domain client.example
media-audit scope add-cidr 192.168.1.0/24
media-audit run external --safe
media-audit report generate --format html,json
```

## Web UI Shape

The local web UI is introduced after the CLI and domain engine are stable.

Recommended V2 stack:
- FastAPI routes
- Jinja2 templates
- HTMX for lightweight interactions
- SQLite persistence
- same services and models as the CLI

The UI must not contain separate business logic. It should call the same domain
services used by the CLI.

Core pages:
- dashboard
- clients
- missions
- mission wizard
- scope management
- check selection
- run monitor
- findings review
- report generation
- settings

## Report Types

Executive report:
- score
- top risks
- business impact
- recommended priorities
- residual risk

Technical report:
- affected assets
- evidence
- reproduction or counter-test
- remediation details
- validation status

Remediation plan:
- quick wins
- priority order
- owner
- expected effort
- counter-test checklist
