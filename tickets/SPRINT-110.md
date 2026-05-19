# Sprint 110 - Debian VM Firewall Plan

## Goal

Help technicians prepare controlled LAN access to the appliance Web UI without
applying firewall rules automatically.

## Scope

- Add `scripts/debian-vm-firewall-plan.sh`.
- Require an explicit `--admin-cidr` value.
- Read `MEDIA_AUDIT_BIND` and `MEDIA_AUDIT_PORT` from `.env` when present.
- Print example UFW commands for review only.
- Remind technicians to keep authentication enabled and preserve management
  access.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper fails when `--admin-cidr` is missing.
- The helper prints a plan and does not execute firewall commands.
- The helper does not use `sudo`, `ufw enable`, `iptables`, or `nft`.
- The helper does not start services, collect logs, install packages, or run
  scanners.
- Documentation explains that LAN exposure requires technician review.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- Firewall changes remain a human-reviewed operational step.
