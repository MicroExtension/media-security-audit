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

Default local URL:

```text
http://127.0.0.1:8080
```

For access from another workstation on the customer LAN, edit `.env`:

```text
MEDIA_AUDIT_BIND=0.0.0.0
MEDIA_AUDIT_PORT=8080
```

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
bash scripts/debian-vm-update.sh
```

The update helper requires the VM clone to be on `main` with no tracked local
changes. It creates a backup first, pulls with `git pull --ff-only`, rebuilds
the image, runs strict preflight, and only then restarts Docker Compose.

Back up persistent folders before customer-impacting updates:

```bash
bash scripts/debian-vm-backup.sh
```

Backups are written to `reports/backups` by default. Set
`MEDIA_AUDIT_BACKUP_DIR=/path/to/backups` to write archives elsewhere.
Verify an archive before relying on it:

```bash
bash scripts/debian-vm-verify-backup.sh reports/backups/media-audit-backup-YYYYMMDDTHHMMSSZ.tgz
```

Add `--verbose` to print the archive listing. The verification helper does not
extract or restore data.
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

## Current Limitations

- The web UI does not execute scans yet.
- Full user management is not implemented yet.
- Docker image signing is not implemented yet.
- Offline update packaging is not implemented yet.
- OVA and VHDX packaging are future targets.
