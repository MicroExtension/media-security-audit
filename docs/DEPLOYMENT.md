# Deployment Guide

MEDIA Security Audit Platform is deployed as a local appliance, not as a public
SaaS service.

Recommended first target:

- private GitHub repository for source control
- Debian 12 or Ubuntu Server LTS VM for customer deployments
- Docker Compose for runtime packaging
- local web UI on port `8080`
- persistent local folders for data, evidence, runs, and reports

## Hosting Model

Use GitHub only to host the private source repository.

Deploy the application on a local VM for each customer or audit environment:

```text
GitHub private repo -> local VM -> Docker Compose -> local web UI
```

Do not expose the UI directly to the public internet. If remote access is
required, use VPN, bastion access, or another controlled administration path.

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

Copy the environment template:

```bash
cp .env.example .env
```

Create persistent folders and assign them to the default container user:

```bash
mkdir -p data runs reports evidence
sudo chown -R 10001:10001 data runs reports evidence
```

Alternative for a technician-owned lab VM: set `MEDIA_AUDIT_UID` and
`MEDIA_AUDIT_GID` in `.env` to the output of `id -u` and `id -g`, then keep the
folders owned by that technician account.

Build and start the service:

```bash
docker compose up -d --build
```

Check service status:

```bash
docker compose ps
docker compose logs -f media-audit
```

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
git pull --ff-only
docker compose up -d --build
```

Back up persistent folders before customer-impacting updates:

```bash
tar -czf media-audit-backup.tgz data runs reports evidence
```

## Current Limitations

- The web UI is read-only.
- Authentication is not implemented yet.
- Docker image signing is not implemented yet.
- Offline update packaging is not implemented yet.
- OVA and VHDX packaging are future targets.
