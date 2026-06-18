# MEDIA Security Audit V1 Release Candidate Procedure

This procedure validates a local Debian/Ubuntu VM before declaring it ready for
a controlled V1 customer pilot.

It does not install packages, collect application logs, read customer file
contents, or run scanners. Live checks remain allowed only after written
authorization, approved scope, and explicit operator confirmation.

## 1. Update the VM Repository

Run from the VM:

```bash
cd ~/media-security-audit
git switch main
git pull --ff-only
```

Expected result:

- the branch is `main`
- there are no tracked local changes
- the VM is on the latest approved release candidate code

## 2. Review Local Security Posture

```bash
bash scripts/debian-vm-security-review.sh
```

Expected result:

- web authentication is enabled
- the web password is configured and stored in the maintenance vault
- the UI binds locally, or access is protected by approved firewall or VPN rules
- `.env` permissions are safe

## 3. Validate Deployment Readiness

```bash
bash scripts/debian-vm-preflight.sh
bash scripts/debian-vm-status.sh
```

Expected result:

- storage is writable
- Docker Compose configuration is valid
- required tooling is ready, or optional missing tooling is documented
- no scanner is executed by these commands

## 4. Start or Restart the Service

For a first start:

```bash
bash scripts/debian-vm-start.sh
```

For an existing service:

```bash
bash scripts/debian-vm-restart.sh --confirm
```

Then verify:

```bash
bash scripts/debian-vm-status.sh
```

Expected result:

- the service is running
- the web interface is reachable on the approved bind address and port
- authentication is still required

## 5. Run the Functional Pilot Workflow

In the web UI:

1. Create or open a pilot client.
2. Create a mission with authorization reference, contact, date, recipients,
   and evidence retention.
3. Add approved scope only.
4. Select the checks required for the pilot.
5. Review Mission Focus, Go/No-Go, readiness, scan plan, and handoff panels.
6. Add at least one reviewed finding or import reviewed evidence if applicable.
7. Generate JSON, Markdown, HTML, and PDF reports.
8. Generate the mission ZIP package and review its manifest.

Do not run live checks unless the written authorization and approved scope are
already recorded in the mission.

## 6. Generate Final Evidence

Run:

```bash
bash scripts/debian-vm-v1-readiness-report.sh
bash scripts/debian-vm-pilot-closeout.sh
bash scripts/debian-vm-release-candidate.sh
```

Then verify the latest release candidate result:

```bash
grep -h 'release_candidate=' reports/release-candidate/media-audit-v1-release-candidate-*.txt | tail -n 1
```

Expected result:

```text
release_candidate=ready
```

If the result is `release_candidate=blocked`, open the latest file under
`reports/release-candidate`, correct the listed blocker, and rerun this section.

## 7. Archive Pilot Evidence

Keep these generated folders with the pilot record:

- `reports/v1-readiness`
- `reports/pilot-closeout`
- `reports/release-candidate`
- latest handoff bundle and sidecar manifest from `reports/handoff`

Do not share `.env`, access tokens, application logs, or customer file contents
unless a separate approved support process explicitly requires them.

## Go/No-Go

The VM can be declared V1 release candidate ready only when:

- `v1_readiness=ready`
- `pilot_closeout=ready`
- `release_candidate=ready`
- web authentication and access controls are validated
- the pilot handoff bundle manifest is present and verified
- any live checks were performed only under written authorization and approved
  scope
