"""Safe sample data used for demos and tests."""

from __future__ import annotations

from datetime import date

from media_security_audit.models import AuditType, Finding, Mission, ScopeItem, ScopeType, Severity


def sample_mission() -> Mission:
    return Mission(
        id="mission_sample",
        client_id="client_sample",
        name="Sample Authorized Audit",
        audit_type=AuditType.EXTERNAL,
        authorization_reference="sample-authorization",
        authorization_contact="Sample Sponsor",
        authorization_date=date(2026, 5, 10),
        authorization_expires_at=date(2026, 6, 10),
        emergency_contact="security@example.invalid",
        report_recipients="owner@example.invalid",
        evidence_retention_days=90,
        scope=[
            ScopeItem(
                id="scope_sample_domain",
                type=ScopeType.DOMAIN,
                value="example.invalid",
                approved=True,
            )
        ],
    )


def sample_findings() -> list[Finding]:
    return [
        Finding(
            id="finding_missing_hsts",
            title="Missing HTTP Strict Transport Security header",
            severity=Severity.MEDIUM,
            affected_asset="https://example.invalid",
            category="http_headers",
            source_module="http_headers",
            proof="The Strict-Transport-Security header was not present in the response.",
            risk="Users may be exposed to protocol downgrade attempts on hostile networks.",
            remediation="Enable the Strict-Transport-Security header with an appropriate max-age.",
            counter_test="Request the URL again and confirm the header is present.",
            confidence=0.9,
        ),
        Finding(
            id="finding_dmarc_none",
            title="DMARC policy does not request enforcement",
            severity=Severity.LOW,
            affected_asset="example.invalid",
            category="dns_mail",
            source_module="dns_mail",
            proof="The DMARC policy is missing or set to p=none.",
            risk="Spoofed emails may be harder for recipients to reject automatically.",
            remediation="Move DMARC gradually toward quarantine or reject after monitoring.",
            counter_test="Query _dmarc.example.invalid and confirm the expected policy.",
            confidence=0.8,
        ),
    ]
