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
- Debian VM env initialization helper script started
- Debian VM password rotation helper script started
- Debian VM security review helper script started
- Debian VM firewall plan helper script started
- Debian VM handoff report helper script started
- Debian VM handoff bundle helper script started
- Debian VM maintenance report helper script started
- Debian VM maintenance bundle helper script started
- Debian VM preflight helper script started
- Debian VM start helper script started
- Debian VM status helper script started
- Debian VM stop helper script started
- Debian VM restart helper script started
- Debian VM backup helper script started
- Debian VM backup inventory helper script started
- Debian VM backup verification helper script started
- Debian VM backup manifest helper script started
- Debian VM backup manifest verification helper script started
- Debian VM restore preview helper script started
- Debian VM diagnostics helper script started
- Debian VM support bundle helper script started
- Debian VM update plan helper script started
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
- Debian VM env helper creates local-only authenticated `.env` files
- Debian VM password rotation helper backs up `.env` and keeps auth enabled
- Debian VM security review helper checks auth, bind, permissions, and Compose
- Debian VM firewall plan helper prints LAN access rules without applying them
- Debian VM handoff report helper summarizes safe readiness and bundle inventory checks
- Debian VM handoff bundle helper packages the handoff report only with a manifest
- Debian VM maintenance report helper aggregates safe pre-maintenance checks with backup and bundle inventories
- Debian VM maintenance bundle helper packages the maintenance report only with a manifest
- Debian VM bundle manifest verification helper checks copied bundle integrity
- Debian VM bundle inventory helper lists shareable bundle manifest status
- Debian VM preflight helper validates Compose and strict preflight before startup
- Debian VM start helper starts service only after strict preflight
- Debian VM status helper reports Compose and preflight state without logs
- Debian VM stop helper requires confirmation and preserves data
- Debian VM restart helper reuses safe stop and strict start helpers
- Debian VM backup helper archives persistent folders before updates
- Debian VM backup inventory helper lists archives and manifest status
- Debian VM backup verification helper validates backup archives without restore
- Debian VM backup manifest helper writes sidecar SHA-256 metadata
- Debian VM backup manifest verification helper checks sidecar integrity
- Debian VM restore preview helper extracts backups away from live data
- Debian VM diagnostics helper records bundle inventory checks without application logs
- Debian VM support bundle helper packages diagnostics only with a manifest
- Debian VM update plan helper checks readiness without applying updates
- Debian VM offline update package helper creates source-only packages with manifests
- Debian VM offline update package verification helper checks sidecar integrity
- Debian VM offline update plan helper checks package readiness without applying updates
- Debian VM update helper backs up, verifies a manifest, and preflights before restart
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
- Debian VM first install can generate a guarded local `.env`
- Debian VM web password rotation is explicit, backed up, and auth-preserving
- Debian VM security review can flag LAN/auth issues without secrets or logs
- Debian VM LAN firewall planning is explicit and requires technician review
- Debian VM handoff reports summarize readiness and bundle inventory without logs or customer files
- Debian VM handoff bundles contain handoff reports and manifests only
- Debian VM maintenance reports summarize readiness with backup and bundle inventories
- Debian VM maintenance bundles contain maintenance reports and manifests only
- Debian VM bundle manifest verification is checksum-only and restore-free
- Debian VM bundle inventory is read-only and manifest-aware
- Debian VM deployment has a guarded pre-start helper script
- Debian VM service startup is guarded by strict preflight
- Debian VM status can be checked without collecting logs or customer content
- Debian VM service stop is explicit and preserves persistent data
- Debian VM service restart is explicit, data-preserving, and preflighted
- Debian VM deployment has a guarded local backup helper script
- Debian VM backup inventory is read-only and manifest-aware
- Debian VM backups can be verified before an update is trusted
- Debian VM backup manifests record size and SHA-256 without extraction
- Debian VM backup manifests can be rechecked against copied archives
- Debian VM backups can be preview-extracted without replacing live data
- Debian VM diagnostics can be collected with bundle inventory status without bundling customer files or logs
- Debian VM support bundles contain diagnostics reports and manifests only
- Debian VM update planning is read-only before approved maintenance
- Debian VM offline update packages can be generated from tracked source only
- Debian VM offline update package manifests can be rechecked before copying
- Debian VM offline update planning can verify package metadata without applying updates
- Debian VM updates are guarded by backup, manifest verification, fast-forward pull, and strict preflight

## Future MSP Differentiators

Potential specialized modules:
- Fortinet configuration review
- Active Directory hygiene checks
- Microsoft 365 baseline checks
- Veeam configuration review
- Synology/QNAP exposure review
- VLAN and segmentation checklist
- backup and restore evidence review
