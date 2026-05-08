# Deployment Strategy

## Deployment Goal

The final product should be deployable as a local audit appliance in customer
environments.

The technician should be able to import a VM, open a browser, create a mission,
run authorized checks, and export reports.

## V1 Local Development

Developer workflow:
- Python virtual environment
- CLI execution
- pytest
- local report outputs

No VM packaging is required in V1.

## V2 Local Web App

Recommended services:
- app: FastAPI + UI
- worker: scanner execution worker later
- database: SQLite volume
- reports volume
- evidence volume

Initial ports:
- web UI: 8080

## V3 Appliance Layout

Target filesystem layout:

```text
/opt/media-audit/
├── app/
├── config/
├── data/
├── evidence/
├── reports/
├── logs/
├── scripts/
└── docker-compose.yml
```

## VM Targets

Supported targets:
- Debian 12
- Ubuntu Server LTS

Hypervisors:
- VMware via OVA
- Hyper-V via VHDX

## Network Modes

Internal audit:
- VM connected to customer internal network
- static IP or DHCP
- browser access from technician workstation

External audit:
- run from MSP infrastructure or controlled external location
- customer-approved public assets only

## Access Model

V2 simple mode:
- local admin account
- password configured during first setup

Later:
- role-based access
- technician accounts
- read-only report viewer

## Update Strategy

V1:
- manual code update

V2:
- Docker image rebuild

V3:
- signed update package
- backup before update
- rollback notes

## Backup Strategy

Back up:
- database
- reports
- evidence
- configuration

Do not back up:
- temporary scanner output
- cache directories

## Customer Data Handling

By default:
- data stays local to the appliance
- reports are exported manually
- no cloud sync
- no telemetry

Any future cloud sync must be explicit and documented.

## First Setup Wizard

The appliance should ask for:
- organization name
- admin password
- default report footer
- timezone
- storage path confirmation
- external tool availability check

## External Tool Check

The UI should show whether these tools are available:
- nmap
- testssl.sh
- smbclient or enum4linux-ng
- Python DNS libraries

Unavailable tools should disable only the related checks.

