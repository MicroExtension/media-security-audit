# Real Condition Test Runbook

Use this runbook for the first controlled customer pilot after the VM is
installed and the V1 readiness report is green.

The goal is to validate the complete operational flow:

```text
VM update -> service health -> guided audit -> guarded checks -> findings review -> reports -> package -> closeout
```

This runbook does not replace written authorization, customer approval, or
human judgment.

## 1. Preconditions

Confirm these items before any live check:

- written authorization is stored outside the application
- the maintenance or audit window is confirmed with the customer
- an emergency contact is reachable during the test
- the approved scope lists only targets that may be contacted
- excluded targets are documented
- web authentication is enabled
- the UI is local-only, VPN-only, or firewall-restricted
- the technician knows how to stop the service and pause testing

Do not continue if authorization, scope, or contact details are unclear.

## 2. Update The VM

Run this from the VM repository directory:

```bash
cd ~/media-security-audit
git switch main
git pull --ff-only
bash scripts/debian-vm-update-plan.sh
bash scripts/debian-vm-backup.sh
bash scripts/debian-vm-update.sh --confirm
```

If the update helper blocks, stop and review the generated action message
before doing manual fixes.

## 3. Validate Runtime Readiness

Run:

```bash
cd ~/media-security-audit
bash scripts/debian-vm-security-review.sh
bash scripts/debian-vm-preflight.sh
bash scripts/debian-vm-start.sh
bash scripts/debian-vm-status.sh
bash scripts/debian-vm-v1-readiness-report.sh
```

Expected state:

- authentication ready
- persistent folders writable
- Docker Compose service running
- Nmap ready
- optional tools either ready or documented
- `v1_readiness=ready` in the latest readiness report

Missing `testssl.sh` or Nuclei can be acceptable for a limited pilot only when
TLS and Nuclei checks are intentionally deferred.

## 4. Open The Web UI

For local-only deployments, use an SSH tunnel from the technician workstation:

```bash
ssh -L 8080:127.0.0.1:8080 mediaadmin@<vm-ip>
```

Then open:

```text
http://127.0.0.1:8080
```

Use the vaulted `MEDIA_AUDIT_WEB_USERNAME` and `MEDIA_AUDIT_WEB_PASSWORD`.

Do not expose the UI directly to the public internet.

## 5. Create The Pilot Audit

From the web UI:

1. Open `Wizard`.
2. Select or create the customer.
3. Enter the mission name and authorization reference.
4. Add the authorization contact and dates when available.
5. Add only approved targets.
6. Select the checks that match the approved targets.
7. Review target coverage.
8. Review `Field Trial Readiness`.
9. Create the guided audit.

Stop if the wizard shows missing target coverage or unclear authorization.

## 6. Review Before Any Live Check

Open the created mission and review:

- `Mission Go/No-Go`
- `Mission Readiness`
- `Scan Launch Center`
- `Scan Plan Preview`
- `Live Trial Guardrails`

For each ready service, confirm:

- the command count is expected
- the command intent matches the customer scope
- the customer window is still active
- the emergency contact is still reachable
- no excluded target appears in the approved target list

## 7. Run Guarded Checks

Run only one service at a time from the mission page.

For each service:

1. Read the pre-launch decision box.
2. Confirm the checkbox only if the command is expected.
3. Run the service.
4. Review `Run Monitor`.
5. Review generated findings and evidence summary.
6. Pause if the output is unexpected or if the customer reports impact.

Do not run checks that are blocked, not selected, out of scope, or not covered
by the customer window.

## 8. Review Findings

After live checks:

1. Open `Findings`.
2. Mark obvious false positives with a technician note.
3. Mark accepted risks only when the customer has explicitly accepted them.
4. Add manual findings for validated issues that were not automatically found.
5. Run CVE/KEV correlation only against collected findings and approved scope.
6. Confirm each critical or high item has a plain-language remediation.

The report should explain the issue, the impact, the remediation, and the
counter-test in terms a customer can act on.

## 9. Generate Outputs

From the mission page, generate and review:

- authorization brief when needed
- JSON report for tracking and remediation follow-up
- HTML or PDF report for human review
- mission export package
- export manifest
- export verification

Confirm the report highlights critical and high findings before detailed
technical sections.

## 10. Close The Pilot Session

Run:

```bash
cd ~/media-security-audit
bash scripts/debian-vm-handoff-report.sh
bash scripts/debian-vm-handoff-bundle.sh
bash scripts/debian-vm-bundle-inventory.sh --verify-manifests
bash scripts/debian-vm-pilot-closeout.sh
```

Expected state:

- latest V1 readiness report is ready
- handoff bundle is present
- handoff manifest is verified
- pilot closeout is ready or has documented blockers

## 11. Go / No-Go Criteria

The pilot is acceptable when:

- no scan ran outside approved scope
- no test ran without explicit authorization confirmation
- Run Monitor shows expected outcomes or documented blockers
- reports were generated and reviewed
- JSON tracking output exists
- remediation guidance is understandable
- package and manifest verification succeeded
- customer-impact notes are empty or documented

The pilot is blocked when:

- authorization is missing or ambiguous
- scope cannot be verified
- UI access is not controlled
- the VM cannot pass deployment preflight
- generated reports are incomplete
- package verification fails
- any live check caused unexpected customer impact

## 12. After The Pilot

Record the pilot result with:

- customer name
- mission ID
- date and time window
- services tested
- services deferred
- blockers
- remediation follow-up owner
- planned counter-test date

Keep customer evidence inside the approved evidence and reports folders. Do not
copy application logs or unrelated customer files into handoff bundles.
