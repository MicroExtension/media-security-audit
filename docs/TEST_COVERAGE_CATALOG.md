# Test Coverage Catalog

This catalog defines the security checks that MEDIA Security Audit should cover
as a safe MSP audit platform.

The product goal is broad, non-destructive coverage with clear remediation.
It is not an automated exploitation or brute-force platform.

## V1 Safe Execution

| Area | Status | Inputs | Output |
| --- | --- | --- | --- |
| Nmap TCP service discovery | implemented guarded path | internal CIDR, IP, hostname | service/version findings and evidence |
| HTTP security headers | implemented guarded path | approved URL | missing or weak header findings |
| DNS/Mail hygiene | implemented guarded path | approved domain | SPF, DKIM, DMARC, MX observations |
| TLS checks | implemented guarded path | approved URL/domain | TLS weakness findings from testssl.sh |
| SMB anonymous exposure | implemented guarded path | approved internal host | anonymous share/listing findings |
| LDAP RootDSE review | implemented guarded path | approved AD/LDAP host | LDAP/LDAPS hygiene findings |
| CVE/KEV correlation | implemented review workflow | local reviewed CVE/KEV catalog and findings | candidate findings requiring validation |
| PDF/JSON/HTML/Markdown reports | implemented | reviewed findings | customer report and remediation tracking |

## V2 Planned Safe Modules

| Area | Intended Coverage |
| --- | --- |
| AD hygiene | LDAP signing, LDAPS availability, anonymous bind exposure, password policy metadata where readable |
| Fortinet/VPN exposure | public management surfaces, TLS posture, version evidence where safely fingerprinted |
| Veeam exposure | console/API exposure and TLS/header hygiene when authorized |
| NAS/Synology/QNAP hygiene | web management exposure, TLS/header posture, public service exposure |
| M365 tenant hygiene | SPF/DKIM/DMARC alignment, admin-controlled export imports, secure score style checklist |
| Nuclei template checks | only after template governance, reviewed templates, pinned versions, and customer authorization |

## Explicitly Excluded Until Separate Governance

The following capabilities are intentionally excluded from normal V1/V2
operation:

- automated exploitation
- password brute force
- credential stuffing
- payload deployment
- privilege escalation
- post-exploitation
- destructive denial-of-service testing
- automatic exfiltration
- unreviewed scanner template updates during an audit

Credential dataset review can exist as a governance and documentation workflow,
but live credential attack automation must remain outside the default product.

## CVE And CVSS Handling

CVE/KEV matches should be explained simply:

1. What product or version appears affected.
2. Why the vulnerability matters.
3. Whether it is known exploited.
4. What evidence still needs validation.
5. What remediation is recommended.
6. How the counter-test should confirm remediation.

CVSS severity helps prioritize, but it is not enough by itself. The report must
also consider exposure, confidence, business impact, and whether the finding was
validated in the approved scope.

## Reporting Requirements

Each finding must keep:

- severity
- confidence
- affected asset
- simple risk explanation
- proof
- remediation advice
- counter-test procedure
- source module
- CVE/KEV reference when applicable
- status for follow-up: new, confirmed, false positive, accepted risk,
  remediated, counter-test passed, or counter-test failed

The JSON report remains the remediation tracking artifact. The PDF report is
the readable customer deliverable.
