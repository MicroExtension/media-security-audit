# Audit Methodology

## Mission Lifecycle

1. Create the client record.
2. Create the mission.
3. Attach written authorization.
4. Define scope.
5. Validate scope.
6. Run non-destructive checks.
7. Normalize findings.
8. Review and suppress false positives.
9. Generate reports.
10. Apply remediation.
11. Run counter-tests.
12. Record residual risk.

## Internal Audit V1

Checks:
- network discovery in authorized CIDRs
- exposed services
- SMBv1 detection
- SMB signing status where safely detectable
- RDP exposure
- LDAP/LDAPS exposure
- TLS weak protocol detection
- NAS, printer, hypervisor, and admin interface exposure

## External Audit V1

Checks:
- public ports
- TLS configuration
- certificate validity
- HTTP headers
- DNS records
- SPF
- DKIM presence
- DMARC policy
- sensitive admin interfaces exposed to the internet
- VPN and firewall exposure inventory

## Finding Quality Bar

A finding is valid only when it has:
- affected asset
- precise observation
- safe evidence
- risk explanation
- remediation guidance
- counter-test guidance
- confidence level

Low-quality findings should be marked for manual review instead of appearing as
definitive results.

