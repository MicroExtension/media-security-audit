"""Form handling helpers for the local web interface."""

from __future__ import annotations

import secrets
from urllib.parse import parse_qs

from media_security_audit.models import (
    AuditType,
    Client,
    Finding,
    FindingStatus,
    Mission,
    ScopeEnvironment,
    ScopeItem,
    ScopeType,
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
    return store.create_mission(
        Mission(
            client_id=required_text(form, "client_id", "client"),
            name=required_text(form, "name", "mission name"),
            audit_type=AuditType(required_text(form, "audit_type", "audit type")),
            authorization_reference=optional_text(form, "authorization_reference"),
            notes=optional_text(form, "notes"),
        )
    )


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


def new_form_token() -> str:
    return secrets.token_urlsafe(32)


def validate_form_token(form: dict[str, str], expected_token: str) -> None:
    submitted = form.get("_csrf", "")
    if not submitted or not secrets.compare_digest(submitted, expected_token):
        raise ValueError("invalid form token")
