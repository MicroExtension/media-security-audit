# Roadmap

## V0 - Agent-Ready Repository

Goal: create a clear project frame for Codex and future contributors.

Deliverables:
- AGENTS.md
- architecture notes
- legal and scope rules
- sprint tickets
- initial Python package metadata
- empty app and test structure

## V1 - CLI Audit Foundation

Goal: reliable CLI, normalized findings, and clean reports.

Features:
- client and mission model
- scope validation
- findings engine
- JSON report
- Markdown report
- HTML report
- safe Nmap adapter
- Nmap XML parser
- HTTP headers audit
- DNS and mail audit
- TLS adapter for testssl.sh

Success criteria:
- no scan can run without a mission and scope
- every finding has remediation and counter-test fields
- parser tests use fixtures
- reports are readable by a non-technical decision maker and useful to a technician

## V2 - Local Web Interface

Goal: make the platform easy to use for technicians without sacrificing the
safe CLI foundation.

Features:
- local FastAPI web app
- dashboard
- client and mission management
- mission creation wizard
- authorization tracking
- scope validation UI
- check selection UI
- run monitor
- findings review workflow
- report generation workflow
- counter-test workflow

Success criteria:
- no scan can be launched without approved scope
- a technician can create a mission in less than 5 minutes
- false positives and accepted risks require notes
- reports can be generated without editing files manually

Current foundation:
- dashboard and mission detail views started
- client detail view started
- client, mission, and scope creation forms started
- mission setup update forms started
- scope review update forms started
- manual finding entry started
- manual finding edit forms started
- finding status review started
- counter-test plan views started
- mission activity log started
- check selection UI started
- structured authorization tracking started
- authorization brief exports started
- run monitor started
- system status page started
- report generation from mission pages started
- mission export packages started
- workspace backup export started
- workspace inventory diagnostics started
- remediation library foundation started
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
- client mission preparation summary started
- dashboard mission preparation summary started
- dashboard client preparation counts started
- dashboard client priority actions started
- dashboard client priority ordering started
- mission preparation columns started
- mission readiness action links started
- mission readiness and safe scan plan previews started
- scan execution remains CLI-only

## V3 - Portable Appliance

Goal: package the platform for repeatable client deployments.

Features:
- Debian/Ubuntu VM image
- Docker Compose deployment
- VMware OVA packaging
- Hyper-V VHDX packaging
- signed update workflow
- remediation library
- recurring audit templates

Current foundation:
- Dockerfile added
- Docker Compose added
- persistent `data`, `runs`, `reports`, and `evidence` folders defined
- deployment guide started in `docs/DEPLOYMENT.md`
- external tool availability status started in the web UI
- mission ZIP export package started
- workspace backup ZIP export started
- workspace integrity diagnostics started
- remediation library foundation started
- remediation library export started
- recurring audit templates started
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
- client mission preparation summary started
- dashboard mission preparation summary started
- dashboard client preparation counts started
- dashboard client priority actions started
- dashboard client priority ordering started
- mission preparation columns started
- mission readiness action links started

Success criteria:
- appliance can run on Debian/Ubuntu
- Docker Compose deployment is documented
- data, evidence, and reports persist across restarts
- backup/export is available
- external tool status is visible in the UI

## Future MSP Differentiators

Potential specialized modules:
- Fortinet configuration review
- Active Directory hygiene checks
- Microsoft 365 baseline checks
- Veeam configuration review
- Synology/QNAP exposure review
- VLAN and segmentation checklist
- backup and restore evidence review
