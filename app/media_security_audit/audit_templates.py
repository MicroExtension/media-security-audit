"""Built-in MSP audit templates."""

from __future__ import annotations

from dataclasses import dataclass

from media_security_audit.models import AuditCheck, AuditType


@dataclass(frozen=True)
class AuditTemplate:
    id: str
    title: str
    audit_type: AuditType
    cadence: str
    summary: str
    recommended_checks: tuple[AuditCheck, ...]
    scope_guidance: tuple[str, ...]
    authorization_requirements: tuple[str, ...]
    deliverables: tuple[str, ...]


BUILTIN_AUDIT_TEMPLATES: tuple[AuditTemplate, ...] = (
    AuditTemplate(
        id="tpl_external_perimeter",
        title="External Perimeter Review",
        audit_type=AuditType.EXTERNAL,
        cadence="quarterly",
        summary="Review public exposure for approved domains, URLs, and internet-facing IPs.",
        recommended_checks=(
            AuditCheck.NMAP,
            AuditCheck.HTTP_HEADERS,
            AuditCheck.DNS_MAIL,
        ),
        scope_guidance=(
            "Approved public IP addresses and hostnames",
            "Approved public URLs for web header review",
            "Approved customer domains for SPF, DKIM, and DMARC checks",
        ),
        authorization_requirements=(
            "Written authorization reference",
            "Public scope validated by the customer",
            "Scan window or maintenance window when required",
        ),
        deliverables=(
            "External exposure summary",
            "Prioritized remediation plan",
            "Counter-test commands for confirmed changes",
        ),
    ),
    AuditTemplate(
        id="tpl_internal_hygiene",
        title="Internal Network Hygiene",
        audit_type=AuditType.INTERNAL,
        cadence="semiannual",
        summary="Review internal service exposure and administrative surface on approved ranges.",
        recommended_checks=(AuditCheck.NMAP,),
        scope_guidance=(
            "Approved internal CIDR ranges",
            "Approved server VLANs or management subnets",
            "Excluded sensitive ranges documented before execution",
        ),
        authorization_requirements=(
            "Written authorization reference",
            "Internal scope owner contact",
            "Emergency stop contact for operations teams",
        ),
        deliverables=(
            "Internal service inventory",
            "Unexpected administrative exposure list",
            "Remediation and counter-test plan",
        ),
    ),
    AuditTemplate(
        id="tpl_web_mail_hygiene",
        title="Web And Mail Hygiene",
        audit_type=AuditType.EXTERNAL,
        cadence="quarterly",
        summary="Focus on browser security headers and mail authentication posture.",
        recommended_checks=(AuditCheck.HTTP_HEADERS, AuditCheck.DNS_MAIL),
        scope_guidance=(
            "Approved HTTPS URLs",
            "Approved customer mail domains",
            "Known DKIM selectors supplied by the customer or MSP",
        ),
        authorization_requirements=(
            "Written authorization reference",
            "Mail platform owner or MSP validation contact",
            "DNS change owner identified for remediation",
        ),
        deliverables=(
            "HTTP header findings",
            "SPF, DKIM, and DMARC findings",
            "DNS and reverse proxy remediation plan",
        ),
    ),
    AuditTemplate(
        id="tpl_remediation_counter_test",
        title="Remediation Counter-Test",
        audit_type=AuditType.MIXED,
        cadence="after remediation",
        summary="Validate corrected findings against the previously approved mission scope.",
        recommended_checks=(
            AuditCheck.NMAP,
            AuditCheck.HTTP_HEADERS,
            AuditCheck.DNS_MAIL,
        ),
        scope_guidance=(
            "Only assets linked to remediated findings",
            "Previously approved scope items still authorized",
            "Changed assets documented in the mission notes",
        ),
        authorization_requirements=(
            "Original authorization still valid or renewed",
            "Remediation owner confirms changes are deployed",
            "Counter-test window agreed with the customer",
        ),
        deliverables=(
            "Counter-test result summary",
            "Remaining residual risk list",
            "Updated remediation status for each finding",
        ),
    ),
)


def list_audit_templates() -> list[AuditTemplate]:
    return sorted(BUILTIN_AUDIT_TEMPLATES, key=lambda item: item.title)


def get_audit_template(template_id: str | None) -> AuditTemplate | None:
    selected_id = (template_id or "").strip()
    if not selected_id:
        return None
    return next((item for item in BUILTIN_AUDIT_TEMPLATES if item.id == selected_id), None)


def filter_audit_templates(
    query: str | None = None,
    audit_type: str | AuditType | None = None,
) -> list[AuditTemplate]:
    query_text = (query or "").strip().lower()
    selected_type = normalize_audit_type(audit_type)
    templates = list_audit_templates()
    if selected_type is not None:
        templates = [item for item in templates if item.audit_type == selected_type]
    if query_text:
        templates = [item for item in templates if query_text in searchable_text(item)]
    return templates


def normalize_audit_type(value: str | AuditType | None) -> AuditType | None:
    if value is None or value == "":
        return None
    if isinstance(value, AuditType):
        return value
    try:
        return AuditType(value.strip())
    except ValueError:
        return None


def searchable_text(template: AuditTemplate) -> str:
    parts = (
        template.id,
        template.title,
        template.audit_type.value,
        template.cadence,
        template.summary,
        " ".join(check.value for check in template.recommended_checks),
        " ".join(template.scope_guidance),
        " ".join(template.authorization_requirements),
        " ".join(template.deliverables),
    )
    return " ".join(parts).lower()
