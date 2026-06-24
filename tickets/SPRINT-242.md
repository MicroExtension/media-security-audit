# Sprint 242 - Final Target And Session Dashboard

## Goal

Move the product closer to the final customer-facing appliance vision:
preconfigured VM delivery, deployment documentation, firewall requirements,
analysis session dashboard, progress percentage, and safe coverage catalog.

## Scope

1. Add a mission analysis session dashboard page.
2. Compute operational progress from authorization, scope, selected services,
   scan runs, CVE/KEV review, reports, and export package readiness.
3. Link the dashboard from mission detail and audit console.
4. Document final VMware/Hyper-V appliance delivery target.
5. Document customer firewall and outbound access requirements.
6. Document safe test coverage and explicitly excluded exploit/brute-force
   capabilities.

## Acceptance Criteria

- A mission exposes `/missions/{mission_id}/session`.
- The session page shows progress percentage, current phase, target counts,
  selected protocols, run dashboard, CVE/KEV summary, and remediation follow-up.
- VM documentation includes OVA/VHDX target, package commands, and customer
  finalization steps.
- Firewall documentation includes default SSH tunnel access, optional LAN UI
  exposure, outbound access, and service-specific audit traffic.
- Test coverage documentation separates safe audit checks from excluded
  exploitation and brute-force capabilities.
- Unit tests cover the route, template, CSS, view model, and documentation.
