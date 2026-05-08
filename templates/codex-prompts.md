# Codex Prompts

## Sprint 1 Prompt

```text
Read AGENTS.md, ROADMAP.md, ARCHITECTURE.md, and tickets/SPRINT-1.md.

Implement Sprint 1 only.

Do not add live scanning yet.

Create:
- Python package under app/media_security_audit
- Typer CLI with --help
- Pydantic models for Client, Mission, ScopeItem, Asset, Finding, Report
- severity enum
- findings engine with deduplication
- JSON export
- Markdown and HTML report renderers
- pytest unit tests

Constraints:
- non-destructive audit platform
- no offensive automation
- no brute force
- no exploitation
- simple typed Python
- keep reports generated from normalized findings
```

## Sprint 2 Prompt

```text
Read AGENTS.md and tickets/SPRINT-2.md.

Implement only the safe Nmap adapter.

Required:
- command builder with safe defaults
- no shell concatenation
- dry-run mode
- XML parser
- fixtures and tests
- findings for risky exposed services

Do not add brute-force NSE scripts, exploit scripts, UDP scan defaults, or
aggressive timing defaults.
```

## Sprint 3 Prompt

```text
Read AGENTS.md and tickets/SPRINT-3.md.

Implement HTTP, DNS, mail, and TLS checks.

Required:
- HTTP headers audit with mocked tests
- DNS SPF, DKIM, DMARC checks with mocked tests
- testssl.sh adapter dry-run and fixture parser
- normalized findings
- report grouping by category

Keep all checks non-destructive and scope-bound.
```

## Sprint 4 Prompt

```text
Read AGENTS.md, PRODUCT_SPEC.md, docs/UI_SPEC.md, and tickets/SPRINT-4.md.

Implement the first local web UI foundation.

Required:
- FastAPI app
- Jinja2 templates
- dashboard
- clients page
- missions page
- mission creation wizard skeleton
- scope management page
- findings review with fixture data
- report generation page

Rules:
- use the same domain services as the CLI
- no scan action without approved scope
- no destructive options
- authorization status must be visible
- keep UI simple and technician-friendly
```

## Sprint 5 Prompt

```text
Read AGENTS.md, docs/DEPLOYMENT.md, and tickets/SPRINT-5.md.

Prepare appliance deployment foundation.

Required:
- Dockerfile
- docker-compose.yml
- persistent volumes
- health check endpoint
- external tool availability check
- backup/export script
- deployment documentation updates

Rules:
- data stays local by default
- reports and evidence persist across restarts
- no telemetry
- no cloud sync
```
