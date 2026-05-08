"""Authentication settings for the local web interface."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import Mapping


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}
PLACEHOLDER_PASSWORDS = {
    "admin",
    "changeme",
    "change-me",
    "change-this-password",
    "password",
    "media-audit",
}


@dataclass(frozen=True)
class WebAuthSettings:
    enabled: bool = False
    username: str = "admin"
    password: str | None = None
    realm: str = "MEDIA Security Audit"


def web_auth_settings_from_env(env: Mapping[str, str] | None = None) -> WebAuthSettings:
    values = os.environ if env is None else env
    enabled = parse_bool(values.get("MEDIA_AUDIT_REQUIRE_AUTH"), default=False)
    username = values.get("MEDIA_AUDIT_WEB_USERNAME", "admin").strip() or "admin"
    password = values.get("MEDIA_AUDIT_WEB_PASSWORD")
    realm = values.get("MEDIA_AUDIT_WEB_REALM", "MEDIA Security Audit").strip()

    settings = WebAuthSettings(
        enabled=enabled,
        username=username,
        password=password,
        realm=realm or "MEDIA Security Audit",
    )
    validate_web_auth_settings(settings)
    return settings


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default

    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise RuntimeError(f"invalid boolean value: {value}")


def validate_web_auth_settings(settings: WebAuthSettings) -> None:
    if not settings.enabled:
        return

    if not settings.username.strip():
        raise RuntimeError(
            "MEDIA_AUDIT_WEB_USERNAME cannot be empty when web authentication is enabled"
        )
    if not settings.password:
        raise RuntimeError("MEDIA_AUDIT_WEB_PASSWORD is required when web authentication is enabled")
    if settings.password.strip().lower() in PLACEHOLDER_PASSWORDS:
        raise RuntimeError("MEDIA_AUDIT_WEB_PASSWORD must be changed before starting the web UI")
    if len(settings.password) < 12:
        raise RuntimeError("MEDIA_AUDIT_WEB_PASSWORD must contain at least 12 characters")


def valid_credentials(settings: WebAuthSettings, username: str | None, password: str | None) -> bool:
    if not settings.enabled:
        return True
    if username is None or password is None or settings.password is None:
        return False
    return secrets.compare_digest(username, settings.username) and secrets.compare_digest(
        password,
        settings.password,
    )
