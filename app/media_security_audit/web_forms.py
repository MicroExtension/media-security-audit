"""Form handling helpers for the local web interface."""

from __future__ import annotations

from datetime import date
import secrets
from urllib.parse import parse_qs

from media_security_audit.audit_templates import get_audit_template
from media_security_audit.models import (
    AuditCheck,
    AuditType,
    Client,
    DEFAULT_AUDIT_CHECKS,
    Finding,
    FindingStatus,
    Mission,
    ScopeEnvironment,
    ScopeItem,
    ScopeType,
    Severity,
    utc_now,
)
from media_security_audit.storage import JsonStore


def parse_urlencoded_form(body: bytes | str) -> dict[str, str]:
    text = body.decode("utf-8") if isinstance(body, bytes) else body
    parsed = parse_qs(text, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def create_client_from_form(store: JsonStore, form: dict[str, str]) -> Client:
    return store.create_client(
        Client(
            name=required_text(form, "name", "client name"),
            internal_reference=optional_text(form, "reference"),
            notes=optional_text(form, "notes"),
        )
    )


def create_mission_from_form(store: JsonStore, form: dict[str, str]) -> Mission:
    template_id = optional_text(form, "audit_template_id")
    template = get_audit_template(template_id)
    if template_id and template is None:
        raise ValueError(f"audit template not found: {template_id}")

    return store.create_mission(
        Mission(
            client_id=required_text(form, "client_id", "client"),
            name=required_text(form, "name", "mission name"),
            audit_type=template.audit_type
            if template
            else AuditType(required_text(form, "audit_type", "audit type")),
            audit_template_id=template.id if template else None,
            authorization_reference=optional_text(form, "authorization_reference"),
            authorization_contact=optional_text(form, "authorization_contact"),
            authorization_date=parse_optional_date(form, "authorization_date"),
            authorization_expires_at=parse_optional_date(form, "authorization_expires_at"),
            emergency_contact=optional_text(form, "emergency_contact"),
            report_recipients=optional_text(form, "report_recipients"),
            evidence_retention_days=parse_optional_int(form, "evidence_retention_days"),
            selected_checks=(
                list(template.recommended_checks) if template else list(DEFAULT_AUDIT_CHECKS)
            ),
            notes=optional_text(form, "notes"),
        )
    )


def update_mission_from_form(store: JsonStore, mission_id: str, form: dict[str, str]) -> Mission:
    mission = store.get_mission(mission_id)
    updates = {
        "name": required_text(form, "name", "mission name"),
        "audit_type": AuditType(required_text(form, "audit_type", "audit type")),
        "authorization_reference": optional_text(form, "authorization_reference"),
        "authorization_contact": optional_text(form, "authorization_contact"),
        "authorization_date": parse_optional_date(form, "authorization_date"),
        "authorization_expires_at": parse_optional_date(form, "authorization_expires_at"),
        "emergency_contact": optional_text(form, "emergency_contact"),
        "report_recipients": optional_text(form, "report_recipients"),
        "evidence_retention_days": parse_optional_int(form, "evidence_retention_days"),
        "notes": optional_text(form, "notes"),
    }
    updated = Mission.model_validate({**mission.model_dump(mode="python"), **updates})
    return store.save_mission(updated)


def update_mission_checks_from_form(
    store: JsonStore,
    mission_id: str,
    form: dict[str, str],
) -> Mission:
    mission = store.get_mission(mission_id)
    selected_checks = [
        check for check in AuditCheck if parse_checkbox(form, f"check_{check.value}")
    ]
    updated = mission.model_copy(update={"selected_checks": selected_checks})
    return store.save_mission(updated)


def add_scope_from_form(store: JsonStore, mission_id: str, form: dict[str, str]) -> Mission:
    return store.add_scope_item(
        mission_id,
        ScopeItem(
            type=ScopeType(required_text(form, "scope_type", "scope type")),
            value=required_text(form, "value", "scope value"),
            environment=ScopeEnvironment(
                optional_text(form, "environment") or ScopeEnvironment.UNKNOWN.value
            ),
            approved=parse_checkbox(form, "approved"),
            excluded=parse_checkbox(form, "excluded"),
            notes=optional_text(form, "notes"),
        ),
    )


def update_scope_from_form(
    store: JsonStore,
    mission_id: str,
    scope_id: str,
    form: dict[str, str],
) -> Mission:
    mission = store.get_mission(mission_id)
    existing = next((item for item in mission.scope if item.id == scope_id), None)
    if existing is None:
        raise FileNotFoundError(f"scope item not found: {scope_id}")

    updated = ScopeItem(
        id=existing.id,
        type=ScopeType(required_text(form, "scope_type", "scope type")),
        value=required_text(form, "value", "scope value"),
        environment=ScopeEnvironment(optional_text(form, "environment") or ScopeEnvironment.UNKNOWN.value),
        approved=parse_checkbox(form, "approved"),
        excluded=parse_checkbox(form, "excluded"),
        notes=optional_text(form, "notes"),
    )
    return store.update_scope_item(mission_id, updated)


def add_manual_finding_from_form(store: JsonStore, mission_id: str, form: dict[str, str]) -> Finding:
    return store.add_finding(
        mission_id,
        Finding(
            title=required_text(form, "title", "finding title"),
            severity=Severity(required_text(form, "severity", "severity")),
            affected_asset=required_text(form, "affected_asset", "affected asset"),
            category=optional_text(form, "category") or "manual",
            source_module="manual",
            proof=required_text(form, "proof", "proof"),
            risk=required_text(form, "risk", "risk"),
            remediation=required_text(form, "remediation", "remediation"),
            counter_test=required_text(form, "counter_test", "counter-test"),
            confidence=parse_confidence(optional_text(form, "confidence")),
        ),
    )


def update_manual_finding_from_form(
    store: JsonStore,
    mission_id: str,
    finding_id: str,
    form: dict[str, str],
) -> Finding:
    existing = store.get_finding(mission_id, finding_id)
    if existing.source_module != "manual":
        raise ValueError("only manual findings can be edited from this form")

    metadata = dict(existing.metadata)
    metadata["edited_at"] = utc_now().isoformat()
    return store.save_finding(
        mission_id,
        Finding(
            id=existing.id,
            title=required_text(form, "title", "finding title"),
            severity=Severity(required_text(form, "severity", "severity")),
            affected_asset=required_text(form, "affected_asset", "affected asset"),
            category=optional_text(form, "category") or "manual",
            source_module=existing.source_module,
            proof=required_text(form, "proof", "proof"),
            risk=required_text(form, "risk", "risk"),
            remediation=required_text(form, "remediation", "remediation"),
            counter_test=required_text(form, "counter_test", "counter-test"),
            confidence=parse_confidence(optional_text(form, "confidence")),
            status=existing.status,
            sources=existing.sources,
            first_seen=existing.first_seen,
            last_seen=utc_now(),
            metadata=metadata,
        ),
    )


def update_finding_status_from_form(
    store: JsonStore,
    mission_id: str,
    finding_id: str,
    form: dict[str, str],
) -> Finding:
    return store.update_finding_status(
        mission_id=mission_id,
        finding_id=finding_id,
        status=FindingStatus(required_text(form, "status", "finding status")),
        review_note=form.get("review_note"),
    )


def required_text(form: dict[str, str], field: str, label: str) -> str:
    value = optional_text(form, field)
    if value is None:
        raise ValueError(f"{label} is required")
    return value


def optional_text(form: dict[str, str], field: str) -> str | None:
    value = form.get(field, "").strip()
    return value or None


def parse_checkbox(form: dict[str, str], field: str) -> bool:
    return form.get(field, "").strip().lower() in {"1", "true", "yes", "on"}


def parse_confidence(value: str | None) -> float:
    if value is None:
        return 0.8
    normalized_value = value.replace(",", ".")
    try:
        return float(normalized_value)
    except ValueError as error:
        raise ValueError("confidence must be a number between 0 and 1") from error


def parse_optional_date(form: dict[str, str], field: str) -> date | None:
    value = optional_text(form, field)
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a valid ISO date") from error


def parse_optional_int(form: dict[str, str], field: str) -> int | None:
    value = optional_text(form, field)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a whole number") from error


def new_form_token() -> str:
    return secrets.token_urlsafe(32)


def validate_form_token(form: dict[str, str], expected_token: str) -> None:
    submitted = form.get("_csrf", "")
    if not submitted or not secrets.compare_digest(submitted, expected_token):
        raise ValueError("invalid form token")
