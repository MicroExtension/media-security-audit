# V1 Test And Deployment Procedure

This procedure explains how to test the V1 pilot and deploy it on a local
customer appliance. The application is a local MSP audit platform, not a public
SaaS service.

Use this document before the first real customer pilot.

## Safety Rules

- Keep the GitHub repository private.
- Keep the web UI local or behind a controlled administration path.
- Do not expose the UI directly to the public internet.
- Do not disable authentication on a customer VM.
- Do not commit `.env`, `data`, `reports`, `runs`, or `evidence`.
- Do not run live scan commands on a customer network without written
  authorization, approved scope, and an approved maintenance window.
- For this V1 validation, prefer dry-run plans, manual findings, reports, and
  handoff bundle checks.

## Target Deployment Model

```text
Private GitHub repository -> local Debian/Ubuntu VM -> Docker Compose -> local web UI
```

Default local URL:

```text
http://127.0.0.1:8080
```

Recommended VM baseline:

- Debian 12 or Ubuntu Server LTS
- 2 vCPU
- 4 GB RAM
- 30 GB disk
- static IP or DHCP reservation
- outbound internet access for first install and updates

## Phase 1 - Test Locally On Windows

Use this phase first on your workstation. It validates the V1 without Docker and
without touching a customer network.

### 1. Clone Or Update The Repository

```powershell
cd "C:\Users\WilliamFromentin-Gir\Documents\Réseau sociaux"
git clone https://github.com/MicroExtension/media-security-audit.git
cd media-security-audit
git switch main
git pull --ff-only
```

If the repository already exists, only run:

```powershell
cd "C:\Users\WilliamFromentin-Gir\Documents\Réseau sociaux\media-security-audit"
git switch main
git pull --ff-only
```

### 2. Create A Python Environment

Python 3.12 or newer is required.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

If PowerShell blocks script activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then reopen PowerShell and activate `.venv` again.

### 3. Run The Automated Test Suite

```powershell
$env:PYTHONPATH='app'
python -m unittest discover -s tests
```

Expected result:

```text
OK
```

If tests fail, stop the validation and fix the failing behavior before customer
deployment.

### 4. Start The Local Web UI

Set temporary authentication for the local test session:

```powershell
$env:MEDIA_AUDIT_REQUIRE_AUTH='true'
$env:MEDIA_AUDIT_WEB_USERNAME='admin'
$env:MEDIA_AUDIT_WEB_PASSWORD='ChangeMe-Local-Test-Only'
python -m media_security_audit.cli web --data-dir data --reports-dir reports --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

Login:

```text
username: admin
password: ChangeMe-Local-Test-Only
```

### 5. Run The Web Smoke Test

From the web UI:

1. Open `System`.
2. Confirm authentication, storage, reports, and tool visibility are shown.
3. Open `Pilot`.
4. Download or open these files:
   - `Summary`
   - `Index`
   - `Receipt`
   - `Final Checklist`
   - `Bundle`
   - `Manifest`
   - `Verify`
5. Confirm the Pilot page shows:
   - readiness counters
   - handoff decision
   - bundle files
   - human and automation file categories
   - manifest file count
6. Return to the dashboard.
7. Create a test client named `V1 Pilot Client`.
8. Create a test mission named `V1 Pilot Audit`.
9. Add authorization details on the mission page.
10. Add one approved scope item, for example:
    - type: `domain`
    - value: `example.test`
    - environment: `external`
    - approved: yes
11. Select safe checks from the mission page.
12. Add a manual finding or sample finding.
13. Review the finding status and notes.
14. Generate reports from the mission page.
15. Generate the mission export package.
16. Open `Exports` and confirm the package is visible.
17. Open the mission export manifest and verification downloads.

Expected result:

- the UI remains responsive
- no live scan is required
- reports are generated
- export package is generated
- manifest and verification pages are downloadable
- Pilot evidence bundle is downloadable
- Final Checklist is downloadable

### 6. Run A CLI Smoke Test

This smoke test uses local test data only.

```powershell
$env:PYTHONPATH='app'
python -m media_security_audit.cli preflight --data-dir data --reports-dir reports
python -m media_security_audit.cli sample-report --output reports\sample
```

Optional mission workflow, after creating a client and mission in the UI:

```powershell
python -m media_security_audit.cli mission readiness --mission-id "mission_xxxxx" --format json
python -m media_security_audit.cli scan plan-all --mission-id "mission_xxxxx" --format json
python -m media_security_audit.cli report generate --mission-id "mission_xxxxx"
python -m media_security_audit.cli mission export-inventory --format json --include-missing
```

Replace `mission_xxxxx` with the mission ID visible in URLs or CLI output.

## Phase 2 - Deploy On A Debian Or Ubuntu VM

Use this phase for the first appliance-style pilot. Run commands on the VM.

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

Add your technician account to the Docker group if needed:

```bash
sudo usermod -aG docker "$USER"
```

Log out and log back in before continuing.

### 2. Clone The Private Repository

```bash
git clone https://github.com/MicroExtension/media-security-audit.git
cd media-security-audit
git switch main
git pull --ff-only
```

### 3. Generate The Local Environment

```bash
bash scripts/debian-vm-init-env.sh
```

The helper creates `.env`, keeps authentication enabled, generates a strong web
password, and binds the UI to `127.0.0.1` by default.

Store the generated password from `.env` in the maintenance password vault.

Do not commit `.env`.

### 4. Review Security Before Startup

```bash
bash scripts/debian-vm-security-review.sh
```

Expected result:

- authentication is enabled
- password is present
- `.env` permissions are acceptable
- binding is local unless you intentionally changed it
- no scanner is executed

### 5. Run Deployment Preflight

```bash
bash scripts/debian-vm-preflight.sh
```

Expected result:

- deployment preflight completes
- persistent folders are ready
- Docker Compose can build the app
- missing `testssl.sh` means TLS live checks are not ready yet, but the V1
  pilot UI, manual findings, reports, exports, and backup workflow can continue
- missing `nuclei` is expected until the future Nuclei module and approved
  templates are enabled
- no scanner is executed

### 6. Start The Service

```bash
bash scripts/debian-vm-start.sh
```

Check status:

```bash
bash scripts/debian-vm-status.sh
```

Check health:

```bash
curl -s http://127.0.0.1:8080/healthz
```

Expected result:

- service is running
- `/healthz` returns coarse readiness only
- no customer data is exposed by `/healthz`

### 7. Open The Web UI

From the VM:

```text
http://127.0.0.1:8080
```

If you need access from an admin workstation on the customer LAN, first prepare
a firewall plan:

```bash
bash scripts/debian-vm-firewall-plan.sh --admin-cidr 192.0.2.0/24
```

Replace `192.0.2.0/24` with the approved administration subnet.

Only after firewall/VPN controls are approved, edit `.env`:

```text
MEDIA_AUDIT_BIND=0.0.0.0
MEDIA_AUDIT_PORT=8080
```

Then restart:

```bash
bash scripts/debian-vm-restart.sh --confirm
```

## Phase 3 - Validate The V1 Pilot On The VM

From the web UI:

1. Login with the credentials stored in the password vault.
2. Open `System`.
3. Confirm auth, storage, reports, inventory, backup, and tool visibility.
4. Open `Pilot`.
5. Download:
   - handoff summary
   - bundle index
   - bundle inventory JSON
   - delivery receipt
   - final handoff checklist
   - evidence bundle ZIP
   - manifest JSON
   - verification Markdown
6. Create a test client.
7. Create a test mission.
8. Record authorization details.
9. Add approved scope.
10. Select safe checks.
11. Add manual or sample findings.
12. Review finding disposition and notes.
13. Generate mission reports.
14. Generate mission export package.
15. Review `Exports`.
16. Download mission package manifest and verification.
17. Create a workspace backup from `System`.
18. Generate a handoff report:

```bash
bash scripts/debian-vm-handoff-report.sh
```

19. Generate a handoff bundle:

```bash
bash scripts/debian-vm-handoff-bundle.sh
```

20. Verify bundle inventory:

```bash
bash scripts/debian-vm-bundle-inventory.sh
```

Expected result:

- pilot files are downloadable
- mission reports are generated
- mission export package is generated
- handoff report and bundle are generated
- bundle inventory shows manifest status
- no live scan is required for this V1 validation

## Phase 4 - V1 Acceptance Criteria

Mark V1 as ready for a controlled internal pilot only if all criteria are true:

- automated tests pass locally
- Docker preflight passes on the VM
- web authentication is enabled
- UI is local-only or protected by approved LAN/VPN controls
- dashboard loads
- system status loads
- pilot page loads
- pilot final handoff checklist downloads
- client creation works
- mission creation works
- authorization details can be recorded
- approved scope can be recorded
- check selection can be recorded
- manual/sample finding workflow works
- reports can be generated
- mission export package can be generated
- export inventory lists the package
- manifest and verification downloads work
- workspace backup can be generated
- handoff report can be generated
- handoff bundle can be generated
- no customer scan was run without explicit authorization

## Phase 5 - Stop Or Restart The VM Service

Stop for maintenance:

```bash
bash scripts/debian-vm-stop.sh --confirm
```

Restart after maintenance:

```bash
bash scripts/debian-vm-restart.sh --confirm
```

Rotate the web password:

```bash
bash scripts/debian-vm-rotate-password.sh --confirm
```

Store the new password in the maintenance password vault.

## Troubleshooting

### Port 8080 Already In Use

Windows local test:

```powershell
python -m media_security_audit.cli web --data-dir data --reports-dir reports --host 127.0.0.1 --port 8081
```

Debian/Ubuntu VM:

Edit `.env`:

```text
MEDIA_AUDIT_PORT=8081
```

Then restart:

```bash
bash scripts/debian-vm-restart.sh --confirm
```

### Login Fails

Check `.env` on the VM:

```bash
grep '^MEDIA_AUDIT_WEB_USERNAME=' .env
grep '^MEDIA_AUDIT_REQUIRE_AUTH=' .env
```

Do not print or share the password in screenshots or tickets.

Rotate the password if needed:

```bash
bash scripts/debian-vm-rotate-password.sh --confirm
bash scripts/debian-vm-restart.sh --confirm
```

### Docker Permission Error

Check that your user is in the Docker group:

```bash
groups
```

If needed:

```bash
sudo usermod -aG docker "$USER"
```

Then log out and log back in.

### Persistent Folder Permission Error

Run:

```bash
mkdir -p data runs reports evidence
sed -i "s/^MEDIA_AUDIT_UID=.*/MEDIA_AUDIT_UID=$(id -u)/" .env
sed -i "s/^MEDIA_AUDIT_GID=.*/MEDIA_AUDIT_GID=$(id -g)/" .env
bash scripts/debian-vm-preflight.sh
```

### Git Pull Fails On The VM

Confirm the VM can access the private repository and that the GitHub account or
deploy key has permission.

```bash
git remote -v
git status
git pull --ff-only
```

## What Requires Product Owner Action

- Run the local Windows test once.
- Prepare or approve the Debian/Ubuntu VM.
- Store the generated web password in the password vault.
- Decide whether the UI remains local-only or is reachable from an admin LAN.
- Approve the administration subnet before any LAN exposure.
- Confirm written authorization and approved scope before any live customer scan.

## Current V1 Recommendation

Use V1 first as a controlled internal pilot:

- create client and mission records
- document authorization and scope
- generate safe scan plans
- enter manual/sample findings
- generate reports
- generate export packages
- validate handoff bundle and final checklist

Treat live scanner execution as a separate approval step, not as part of the
first V1 deployment validation.
