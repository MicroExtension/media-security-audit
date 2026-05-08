# MEDIA Security Audit Platform

## Mission

Build an internal MSP security audit platform for authorized maintenance clients.

The product is an audit and remediation support platform, not an offensive
pentest automation framework.

Primary users:
- MSP operators
- security technicians
- ExpertCyber-style service teams
- local authorities and SMB customers under maintenance contracts

## Core Principles

- Authorization first: every run must be attached to a mission and approved scope.
- Non-destructive checks only.
- No brute force.
- No automatic exploitation.
- No payload deployment.
- No exfiltration.
- No privilege escalation automation.
- No denial-of-service behavior.
- Evidence must be limited, relevant, and safe to store.
- Every finding must include risk, proof, remediation, and counter-test steps.

## V1 Scope

V1 is CLI-first.

Required capabilities:
- client and mission management
- scope management for CIDR, IP, host, domain, and URL targets
- safe Nmap wrapper
- Nmap XML parsing
- HTTP header audit
- DNS and mail audit for SPF, DKIM, and DMARC
- TLS audit adapter for testssl.sh
- basic SMB audit adapter
- generic findings engine
- JSON report export
- Markdown and HTML report export
- execution logs

## Recommended Stack

- Python 3.12+
- Typer for CLI
- FastAPI for the local web UI
- Pydantic for models
- Jinja2 and HTMX for the first GUI
- SQLite later for persistence
- Jinja2 for reports
- pytest for tests
- Docker for reproducible dependencies
- Debian 12 or Ubuntu Server LTS as VM target

## Architecture Rules

- Keep scanner adapters isolated from the domain model.
- Never build shell commands by concatenating untrusted input.
- Validate scope before executing any external command.
- Store raw evidence separately from normalized findings.
- Findings are the stable internal contract.
- Reports must be generated from normalized findings, not raw tool output.
- Prefer deterministic tests with fixtures over live network tests.

## Finding Contract

Each finding must contain:
- stable id
- title
- severity
- affected asset
- category
- source module
- proof
- risk
- remediation
- counter-test command or procedure
- confidence
- timestamps

## Severity Model

Use a simplified severity model for V1:
- critical
- high
- medium
- low
- info

Do not claim exploitability unless the check proves it safely.

## External Tools Policy

Allowed V1 tools:
- nmap
- testssl.sh
- dns Python libraries
- smbclient or enum4linux-ng in safe modes
- nuclei only with safe, explicitly selected templates

Avoid in V1:
- Metasploit automation
- brute-force tools
- exploit PoCs
- destructive scanners
- password spraying
- credential stuffing
- post-exploitation frameworks

## Reporting Priorities

Reports must be useful for remediation:
- executive summary
- technical details
- prioritized remediation plan
- quick wins
- residual risks
- counter-test checklist

The report quality matters more than the number of checks.

## Coding Style

- Simple, typed Python.
- Small modules.
- Explicit errors.
- Structured logging.
- Unit tests for parsing, findings, scope validation, and report generation.
- Avoid clever abstractions before the second implementation needs them.

## Work Method

Build in small Codex tasks:
1. project skeleton and domain models
2. findings engine
3. Nmap safe wrapper and XML parser
4. report generation
5. HTTP/DNS/TLS modules
6. SMB/LDAP/AD safe modules
7. local web UI after CLI and domain services are stable
8. appliance packaging after the web UI is usable

## GUI Rules

- The GUI must use the same domain services as the CLI.
- The GUI must be local-first and able to run inside the appliance VM.
- The GUI must not expose destructive options.
- Scan buttons must be disabled until mission scope is approved.
- Authorization status must be visible before any run.
- Report generation must warn about unreviewed critical or high findings.
- False positives and accepted risks require technician notes.
