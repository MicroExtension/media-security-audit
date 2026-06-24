# Customer Firewall Requirements

This document describes the network flows to review before deploying the MEDIA
Security Audit VM at a customer site.

## Default Secure Mode

Default mode keeps the web UI local to the VM:

```text
MEDIA_AUDIT_BIND=127.0.0.1
MEDIA_AUDIT_PORT=8080
```

Technicians should access the UI through SSH port forwarding:

```bash
ssh -L 8080:127.0.0.1:8080 mediaadmin@<vm-ip>
```

Browser URL:

```text
http://127.0.0.1:8080/test-readiness
```

No inbound customer firewall opening is required in this mode beyond the
approved administration path to the VM.

## Optional LAN UI Access

Only use LAN UI exposure after customer approval:

```text
MEDIA_AUDIT_BIND=0.0.0.0
MEDIA_AUDIT_PORT=8080
```

Restrict access to the approved administration subnet or VPN only. Generate a
review plan before applying firewall changes:

```bash
bash scripts/debian-vm-firewall-plan.sh --admin-cidr <approved-admin-cidr>
```

The helper prints firewall commands for review and does not apply rules.

## Outbound Access

Recommended outbound access from the VM:

| Destination | Protocol | Purpose |
| --- | --- | --- |
| GitHub private repository | HTTPS 443 | Source updates and first install |
| Linux distribution mirrors | HTTP/HTTPS 80/443 | OS package updates |
| Docker image registry | HTTPS 443 | Base image pulls during build |
| CISA KEV catalog source | HTTPS 443 | Optional reviewed CVE/KEV refresh |
| Customer-approved targets | Customer-approved ports only | Authorized internal or external audit checks |

If outbound internet is not allowed, use the offline update package workflow in
`docs/DEPLOYMENT.md`.

## Internal Audit Traffic

Internal checks must be limited to the approved scope and selected services.
Typical destination ports depend on the services selected:

| Service | Typical Ports | Notes |
| --- | --- | --- |
| Nmap TCP discovery | selected TCP ports | No UDP, aggressive mode, or NSE scripts by default |
| HTTP headers | 80, 443, custom HTTP ports | URL scope required |
| TLS | 443, custom TLS ports | Uses approved URL/domain targets |
| DNS/Mail | 53, public DNS/mail records | Domain scope required |
| SMB | 445 | Internal approved hosts only |
| LDAP | 389, 636 | AD/LDAP hosts only |

Do not open broad access without a written scope and a customer-approved test
window.

## External Audit Traffic

External mode is for public IPs, public domains, and public URLs owned or
authorized by the customer. Confirm that:

- the tested public IPs are customer-controlled or explicitly authorized
- the customer expects source traffic from the VM or audit network
- rate-sensitive systems are identified before launch
- VPN/firewall appliances are included only when authorized

## Documentation To Keep With The Customer File

Store the following after each deployment:

- approved scope and authorization reference
- final VM IP and UI access mode
- firewall or VPN rule reference
- smoke test report from `reports/test-readiness`
- generated PDF report
- generated JSON report for remediation tracking
- mission export package manifest
