# Deployment Guide

MEDIA Security Audit Platform is deployed as a local appliance, not as a public
SaaS service.

Recommended first target:

- private GitHub repository for source control
- Debian 12 or Ubuntu Server LTS VM for customer deployments
- Docker Compose for runtime packaging
- local web UI on port `8080`
- persistent local folders for data, evidence, runs, and reports
- local `/healthz` endpoint for Docker and VM readiness monitoring

## Hosting Model

Use GitHub only to host the private source repository.

Deploy the application on a local VM for each customer or audit environment:

```text
GitHub private repo -> local VM -> Docker Compose -> local web UI
```

Do not expose the UI directly to the public internet. If remote access is
required, use VPN, bastion access, or another controlled administration path.

The `/healthz` endpoint is intentionally unauthenticated and only returns
coarse service and storage readiness statuses. It does not expose customer data
or absolute filesystem paths.

## VM Baseline

Recommended minimum VM:

- Debian 12 or Ubuntu Server LTS
- 2 vCPU
- 4 GB RAM
- 30 GB disk
- static IP or DHCP reservation
- outbound internet access for first install and updates

Recommended production access:

- bind UI to `127.0.0.1` for local-only use, or
- bind UI to `0.0.0.0` only behind a host firewall or VPN

## First Install

Clone the private repository on the VM:

```bash
git clone https://github.com/MicroExtension/media-security-audit.git
cd media-security-audit
```

Generate the first local environment file:

```bash
bash scripts/debian-vm-init-env.sh
```

The helper refuses to overwrite an existing `.env`, keeps the UI bound to
`127.0.0.1`, enables authentication, generates a strong
`MEDIA_AUDIT_WEB_PASSWORD`, and restricts file permissions to the current user.
Store the generated password from `.env` in the maintenance password vault
before customer use.

Rotate the web password during an approved maintenance window:

```bash
bash scripts/debian-vm-rotate-password.sh --confirm
```

The rotation helper creates a timestamped `.env` backup, generates a new strong
`MEDIA_AUDIT_WEB_PASSWORD`, keeps `MEDIA_AUDIT_REQUIRE_AUTH=true`, and does not
restart the service automatically. Store the updated password from `.env` in
the maintenance password vault, then restart the service when ready.

Review the VM security posture before customer handoff:

```bash
bash scripts/debian-vm-security-review.sh
```

The review helper checks `.env` permissions, authentication settings, password
presence, LAN binding, and Docker Compose configuration. It does not print
secrets, collect application logs, start services, or run scanners.

Manual alternative:

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

Then edit `.env`:

```text
MEDIA_AUDIT_REQUIRE_AUTH=true
MEDIA_AUDIT_WEB_USERNAME=admin
MEDIA_AUDIT_WEB_PASSWORD=replace-with-the-generated-password
```

Create persistent folders and assign them to the default container user:

```bash
mkdir -p data runs reports evidence
sudo chown -R 10001:10001 data runs reports evidence
```

Alternative for a technician-owned lab VM: set `MEDIA_AUDIT_UID` and
`MEDIA_AUDIT_GID` in `.env` to the output of `id -u` and `id -g`, then keep the
folders owned by that technician account.

Run a local preflight before customer use:

```bash
docker compose run --rm media-audit preflight \
  --data-dir /var/lib/media-audit/data \
  --reports-dir /var/lib/media-audit/reports
```

For a Debian/Ubuntu VM, the guarded helper performs the Compose validation,
local folder checks, image build, and strict preflight in one step:

```bash
bash scripts/debian-vm-preflight.sh
```

The preflight checks local storage, web authentication settings, workspace
inventory, and tool availability. It does not execute scanners.
Use `--format json` when an install script or monitoring wrapper needs a
machine-readable result. JSON output includes `schema_version`, overall
`status`, per-status `summary` counts, and the detailed check `items`. Each
item includes a short `action` field for the technician or install script.
Use `--strict` when warnings should fail a pre-production install gate.

Build and start the service after strict preflight:

```bash
bash scripts/debian-vm-start.sh
```

Check service status:

```bash
bash scripts/debian-vm-status.sh
```

The status helper reports `.env` readiness, Docker Compose configuration,
service status, and deployment preflight JSON. It does not collect application
logs or customer file contents.

Stop the local service for maintenance:

```bash
bash scripts/debian-vm-stop.sh --confirm
```

The stop helper uses `docker compose stop media-audit`. It does not remove
containers, images, volumes, or persistent folders.

Restart the local service after approved maintenance:

```bash
bash scripts/debian-vm-restart.sh --confirm
```

The restart helper calls the guarded stop helper, then starts the service
through the strict preflight start helper.

Default local URL:

```text
http://127.0.0.1:8080
```

For access from another workstation on the customer LAN, edit `.env`:

```text
MEDIA_AUDIT_BIND=0.0.0.0
MEDIA_AUDIT_PORT=8080
```

Generate a firewall plan before exposing the UI:

```bash
bash scripts/debian-vm-firewall-plan.sh --admin-cidr 192.0.2.0/24
```

The firewall plan helper prints example UFW commands for technician review
only. It does not apply firewall rules, start services, collect logs, or run
scanners. Replace `192.0.2.0/24` with the approved administration subnet.

Generate a handoff report before customer use:

```bash
bash scripts/debian-vm-handoff-report.sh
```

Handoff reports are written to `reports/handoff` by default. Set
`MEDIA_AUDIT_HANDOFF_DIR=/path/to/handoff` to write them elsewhere. The helper
runs the security review and deployment status helpers, then records technician
review reminders without collecting application logs or customer file contents.

Create a shareable handoff bundle:

```bash
bash scripts/debian-vm-handoff-bundle.sh
```

Handoff bundles are written to `reports/handoff` by default. Set
`MEDIA_AUDIT_HANDOFF_BUNDLE_DIR=/path/to/handoff-bundles` to write them
elsewhere. The helper generates a fresh handoff report and archives only that
report. It also writes `<bundle.tgz>.manifest.txt` with the bundle name, size,
SHA-256, and source report; review both files before sharing them outside the
customer site.

Verify the handoff bundle manifest after copying the bundle:

```bash
bash scripts/debian-vm-verify-bundle-manifest.sh reports/handoff/media-audit-handoff-YYYYMMDDTHHMMSSZ.tgz
```

Generate a pre-maintenance report before an approved change:

```bash
bash scripts/debian-vm-maintenance-report.sh
```

Maintenance reports are written to `reports/maintenance` by default. Set
`MEDIA_AUDIT_MAINTENANCE_DIR=/path/to/maintenance` to write them elsewhere.
The helper runs the security review, backup inventory with manifest
verification, bundle inventory with manifest verification, and update plan
helpers. It does not start services, collect application logs, extract backups,
restore data, or run scanners.

Create a shareable maintenance bundle:

```bash
bash scripts/debian-vm-maintenance-bundle.sh
```

Maintenance bundles are written to `reports/maintenance` by default. Set
`MEDIA_AUDIT_MAINTENANCE_BUNDLE_DIR=/path/to/maintenance-bundles` to write them
elsewhere. The helper generates a fresh maintenance report and archives only
that report. It also writes `<bundle.tgz>.manifest.txt` with the bundle name,
size, SHA-256, and source report; review both files before sharing them outside
the customer site.

Verify the maintenance bundle manifest after copying the bundle:

```bash
bash scripts/debian-vm-verify-bundle-manifest.sh reports/maintenance/media-audit-maintenance-YYYYMMDDTHHMMSSZ.tgz
```

List all local shareable bundles and manifest status:

```bash
bash scripts/debian-vm-bundle-inventory.sh
bash scripts/debian-vm-bundle-inventory.sh --verify-manifests
```

The bundle inventory helper is read-only. It does not delete bundles, extract
archives, restore data, collect logs, or run scanners.

Then restart:

```bash
docker compose up -d
```

Open:

```text
http://VM-IP:8080
```

The browser will ask for the username and password configured in `.env`.

After login, open the System page from the top navigation to verify local
storage, web authentication, and external tool availability. The status page
only checks local paths and whether executables are present in `PATH`; it does
not launch scanner commands or contact customer targets.

## Web Authentication

Docker deployments require HTTP Basic authentication by default:

```text
MEDIA_AUDIT_REQUIRE_AUTH=true
MEDIA_AUDIT_WEB_USERNAME=admin
MEDIA_AUDIT_WEB_PASSWORD=strong-random-password
```

The application refuses to start if authentication is enabled and the password
is missing, too short, or left as a common placeholder.

For a localhost-only development workstation, authentication can be disabled:

```text
MEDIA_AUDIT_REQUIRE_AUTH=false
```

Do not disable authentication when binding the UI to a LAN interface.

## Persistent Folders

Docker Compose mounts these host folders:

```text
data/      application JSON store
runs/      scan run outputs
reports/   exported reports
evidence/  scanner evidence files
```

These folders are intentionally ignored by Git.

## CLI Commands In Docker

Use `docker compose run --rm` for one-off CLI operations.

Create a client:

```bash
docker compose run --rm media-audit \
  media-audit client create \
  --data-dir /var/lib/media-audit/data \
  --name "Client X" \
  --reference "CLIENT-001"
```

Create an authorized mission:

```bash
docker compose run --rm media-audit \
  media-audit mission create \
  --data-dir /var/lib/media-audit/data \
  --client-id "client_xxxxx" \
  --name "Audit externe" \
  --audit-type external \
  --authorization-reference "AUTH-001"
```

Add approved scope:

```bash
docker compose run --rm media-audit \
  media-audit scope add \
  --data-dir /var/lib/media-audit/data \
  --mission-id "mission_xxxxx" \
  --type domain \
  --value client.example \
  --environment external \
  --approved
```

Generate reports:

```bash
docker compose run --rm media-audit \
  media-audit report generate \
  --data-dir /var/lib/media-audit/data \
  --mission-id "mission_xxxxx" \
  --output /var/lib/media-audit/reports
```

Reviewed reports can also be generated from the mission page in the web UI.
Web-generated report files are written under the mounted `reports/` folder.
Mission export packages can also be generated from the mission page. These ZIP
files include local mission JSON data, findings, activity, run history, and any
already generated report files.

## Safe Scanner Execution

Scanner execution remains guarded by the application.

Nmap planning does not execute scans:

```bash
docker compose run --rm media-audit \
  media-audit scan nmap-plan \
  --data-dir /var/lib/media-audit/data \
  --mission-id "mission_xxxxx" \
  --output-dir /var/lib/media-audit/evidence
```

Nmap execution requires `--execute`, mission authorization, and approved scope:

```bash
docker compose run --rm media-audit \
  media-audit scan nmap-run \
  --data-dir /var/lib/media-audit/data \
  --mission-id "mission_xxxxx" \
  --output-dir /var/lib/media-audit/evidence \
  --execute
```

## Updates

Pull the latest approved version and rebuild:

```bash
bash scripts/debian-vm-update-plan.sh
bash scripts/debian-vm-update.sh
```

The update plan helper is read-only. It checks the current branch, tracked
changes, `.env`, authentication, local backup readiness, and whether the latest
backup has a sidecar manifest, then prints the reviewed commands for the
technician. It does not pull code, build images, restart services, collect
logs, or run scanners.

The update helper requires the VM clone to be on `main` with no tracked local
changes. It creates a backup first, writes and verifies a sidecar manifest,
pulls with `git pull --ff-only`, rebuilds the image, runs strict preflight, and
only then restarts Docker Compose.

Back up persistent folders before customer-impacting updates:

```bash
bash scripts/debian-vm-backup.sh
```

Backups are written to `reports/backups` by default. Set
`MEDIA_AUDIT_BACKUP_DIR=/path/to/backups` to write archives elsewhere.
List local backups and their sidecar manifest status:

```bash
bash scripts/debian-vm-backup-inventory.sh
bash scripts/debian-vm-backup-inventory.sh --verify-manifests
```

The inventory helper is read-only. It does not delete backups, extract
archives, restore data, collect logs, or run scanners.

Verify an archive before relying on it:

```bash
bash scripts/debian-vm-verify-backup.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
```

Add `--verbose` to print the archive listing. The verification helper does not
extract or restore data.

Generate a sidecar manifest before copying a backup archive:

```bash
bash scripts/debian-vm-backup-manifest.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
```

The manifest helper verifies the archive first, then writes
`<backup.tgz>.manifest.txt` with archive name, size, SHA-256, and verification
status. It does not extract or restore data.

Verify the sidecar manifest before relying on a copied backup:

```bash
bash scripts/debian-vm-verify-backup-manifest.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
```

The manifest verification helper compares the manifest archive name, size,
SHA-256, and verification flag against the backup without extracting data.

To inspect the contents in a separate folder without replacing live data:

```bash
bash scripts/debian-vm-restore-preview.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
```

Restore previews are written under `reports/restore-previews` by default. The
helper refuses to extract directly over `data`, `runs`, `reports`, or
`evidence`.

## Diagnostics

Generate a local support report when troubleshooting a VM:

```bash
bash scripts/debian-vm-diagnostics.sh
```

Diagnostics are written to `reports/support` by default. Set
`MEDIA_AUDIT_SUPPORT_DIR=/path/to/support` to write them elsewhere. The helper
collects Git state, Docker Compose status, persistent folder sizes, and
deployment preflight JSON. It does not include application logs or customer
file contents by default.

Create a shareable support bundle after generating diagnostics:

```bash
bash scripts/debian-vm-support-bundle.sh
```

Support bundles are written to `reports/support` by default. Set
`MEDIA_AUDIT_SUPPORT_BUNDLE_DIR=/path/to/support-bundles` to write them
elsewhere. The helper generates a fresh diagnostics report and archives only
that report. It also writes `<bundle.tgz>.manifest.txt` with the bundle name,
size, SHA-256, and source report; review both files before sharing them outside
the customer site.

Verify the support bundle manifest after copying the bundle:

```bash
bash scripts/debian-vm-verify-bundle-manifest.sh reports/support/media-audit-support-YYYYMMDDTHHMMSSZ.tgz
```

## Current Limitations

- The web UI does not execute scans yet.
- Full user management is not implemented yet.
- Docker image signing is not implemented yet.
- Offline update packaging is not implemented yet.
- OVA and VHDX packaging are future targets.
