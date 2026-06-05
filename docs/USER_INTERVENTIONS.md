# User Interventions Needed

This file tracks decisions that require the product owner.

## Needed Now

No blocking decision is needed to continue Sprint 1.

The project can proceed with:
- Python
- Typer CLI
- Pydantic models
- JSON/Markdown/HTML reports
- file-based storage for the first implementation

Current owner action:
- keep the GitHub repository private
- wait for Codex to push working branches
- review the CLI workflow when requested

## Needed Before Branding

Decide:
- final product name
- company display name
- report footer text
- logo file
- color direction for reports and UI

Default assumption until decided:
- product name: MEDIA Security Audit Platform
- organization: M.E.D.I.A.

## Needed Before Real Client Audits

Provide:
- standard customer authorization template
- maintenance contract wording or constraints
- emergency contact process
- data retention policy
- report recipient policy

Default assumption until decided:
- evidence and reports stay local
- no cloud upload
- manual export only

## Needed Before Scanner Modules

Decide safe defaults:
- allowed Nmap timing level
- whether service/version detection is allowed by default
- whether UDP checks are excluded by default
- allowed audit windows
- customer notification procedure
- whether `testssl.sh` is installed during VM preparation or only before TLS
  live checks
- whether the future Nuclei module is approved, including pinned install source
  and reviewed template governance

Default assumption until decided:
- conservative TCP-only checks
- no UDP by default
- no aggressive timing
- no intrusive scripts
- `testssl.sh` is installed only when TLS live checks are approved
- Nuclei remains disabled until template governance is approved

## Needed Before GUI V2

Choose UI priority:
- technician-only interface
- customer-facing presentation mode
- both

Default assumption until decided:
- technician-first interface
- reports are the customer-facing artifact

## Needed Before Appliance V3

Decide:
- VMware first or Hyper-V first
- offline installation requirement
- update mechanism
- offline update package approval process
- offline update package signing requirement
- backup location
- admin password reset process

Default assumption until decided:
- Docker Compose on Debian/Ubuntu
- VMware and Hyper-V documented after app stabilizes
