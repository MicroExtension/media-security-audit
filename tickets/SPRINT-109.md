# Sprint 109 - Debian VM Security Review

## Goal

Give technicians a read-only local review before handing a VM to a customer
environment.

## Scope

- Add `scripts/debian-vm-security-review.sh`.
- Check `.env` existence and permissions.
- Check that Web authentication remains enabled.
- Check that a Web password is present without printing it.
- Warn when the UI is bound to `0.0.0.0`.
- Validate Docker Compose configuration without starting services.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper exits non-zero when blocked checks are present.
- The helper reports warnings for LAN exposure that requires firewall or VPN
  controls.
- The helper does not print `MEDIA_AUDIT_WEB_PASSWORD`.
- The helper does not collect application logs.
- The helper does not start services, install packages, or run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted by the application.
- The helper is intended for customer handoff review only.
