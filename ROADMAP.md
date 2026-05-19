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
- finding review note guardrails started
- mission finding disposition summary started
- counter-test plan views started
- mission activity log started
- check selection UI started
- structured authorization tracking started
- authorization brief exports started
- run monitor started
- system status page started
- report generation from mission pages started
- report finding disposition summary started
- mission export packages started
- workspace backup export started
- workspace inventory diagnostics started
- remediation library foundation started
- remediation suggestions on findings started
- remediation library export started
- audit template library started
- template-assisted mission creation started
- mission template guidance started
- dashboard shortcut count badges started
- dashboard watchlist action links started
- dashboard mission row action links started
- client preparation action links started
- mission page shortcut links started
- client page shortcut links started
- mission context links started
- activity log context links started
- activity log active filter summary started
- activity log page shortcuts started
- remediation library page shortcuts started
- audit template page shortcuts started
- system status page shortcuts started
- active top navigation started
- keyboard skip link started
- visible keyboard focus styles started
- shared layout accessibility landmarks started
- accessible table captions started
- in-page anchor target context started
- accessible form labels started
- accessible form field groups started
- required field indicators started
- deployment healthcheck detail started
- deployment preflight CLI started
- deployment preflight JSON output started
- deployment preflight JSON schema summary started
- deployment preflight remediation actions started
- deployment preflight strict mode started
- Debian VM preflight helper script started
- Debian VM backup helper script started
- Debian VM backup verification helper script started
- Debian VM update helper script started
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
- dashboard shortcut links started
- dashboard client priority summary started
- dashboard client risk level summary started
- dashboard ready missions watchlist started
- dashboard review missions watchlist started
- dashboard blocked missions watchlist started
- dashboard no-mission clients watchlist started
- dashboard blocked clients watchlist started
- dashboard top risk clients watchlist started
- dashboard review backlog clients watchlist started
- dashboard client preparation counts started
- dashboard client finding review counts started
- dashboard client risk summary started
- dashboard client priority actions started
- dashboard client priority ordering started
- dashboard client risk ordering started
- mission preparation columns started
- mission row review count badges started
- mission readiness action links started
- finding review note guardrails started
- mission finding disposition summary started
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
- deployment healthcheck reports storage readiness
- deployment preflight CLI reports local readiness
- deployment preflight JSON output supports automation
- deployment preflight JSON output exposes schema version and status counts
- deployment preflight items include technician remediation actions
- deployment preflight strict mode supports install gates
- Debian VM preflight helper validates Compose and strict preflight before startup
- Debian VM backup helper archives persistent folders before updates
- Debian VM backup verification helper validates backup archives without restore
- Debian VM update helper backs up and preflights before restart
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
- finding review note guardrails started
- mission finding disposition summary started

Success criteria:
- appliance can run on Debian/Ubuntu
- Docker Compose deployment is documented
- data, evidence, and reports persist across restarts
- backup/export is available
- external tool status is visible in the UI
- deployment healthcheck reports coarse storage readiness
- deployment preflight can be run before customer use
- deployment preflight can be consumed by scripts
- deployment preflight JSON schema stays stable for install automation
- deployment preflight explains the next action for warning and blocked checks
- deployment preflight can fail on warnings when strict mode is requested
- Debian VM deployment has a guarded pre-start helper script
- Debian VM deployment has a guarded local backup helper script
- Debian VM backups can be verified before an update is trusted
- Debian VM updates are guarded by backup, fast-forward pull, and strict preflight

## Future MSP Differentiators

Potential specialized modules:
- Fortinet configuration review
- Active Directory hygiene checks
- Microsoft 365 baseline checks
- Veeam configuration review
- Synology/QNAP exposure review
- VLAN and segmentation checklist
- backup and restore evidence review
