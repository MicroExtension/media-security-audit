"""View helpers for audit template pages."""

from __future__ import annotations

from dataclasses import dataclass

from media_security_audit.audit_templates import AuditTemplate, filter_audit_templates
from media_security_audit.models import AuditCheck, AuditType


CHECK_LABELS: dict[AuditCheck, str] = {
    AuditCheck.NMAP: "Nmap services",
    AuditCheck.HTTP_HEADERS: "HTTP headers",
    AuditCheck.DNS_MAIL: "DNS/Mail",
    AuditCheck.TLS: "TLS posture",
    AuditCheck.SMB: "SMB basic",
}


@dataclass(frozen=True)
class AuditTemplateCard:
    id: str
    title: str
    audit_type: str
    cadence: str
    summary: str
    recommended_checks: list[str]
    scope_guidance: tuple[str, ...]
    authorization_requirements: tuple[str, ...]
    deliverables: tuple[str, ...]


@dataclass(frozen=True)
class AuditTemplateLibraryView:
    templates: list[AuditTemplateCard]
    audit_types: list[str]
    selected_audit_type: str
    query: str
    total_count: int


def build_audit_template_library_view(
    query: str | None = None,
    audit_type: str | None = None,
) -> AuditTemplateLibraryView:
    query_text = (query or "").strip()
    selected_audit_type = (audit_type or "").strip()
    templates = filter_audit_templates(query=query_text, audit_type=selected_audit_type)
    return AuditTemplateLibraryView(
        templates=[audit_template_card(item) for item in templates],
        audit_types=[item.value for item in AuditType],
        selected_audit_type=selected_audit_type,
        query=query_text,
        total_count=len(templates),
    )


def audit_template_card(template: AuditTemplate) -> AuditTemplateCard:
    return AuditTemplateCard(
        id=template.id,
        title=template.title,
        audit_type=template.audit_type.value,
        cadence=template.cadence,
        summary=template.summary,
        recommended_checks=[CHECK_LABELS[check] for check in template.recommended_checks],
        scope_guidance=template.scope_guidance,
        authorization_requirements=template.authorization_requirements,
        deliverables=template.deliverables,
    )
