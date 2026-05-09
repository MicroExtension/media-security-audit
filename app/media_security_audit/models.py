"""Domain models for MEDIA Security Audit Platform."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from ipaddress import ip_address, ip_network
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


SEVERITY_RANK: dict[Severity, int] = {
    Severity.CRITICAL: 5,
    Severity.HIGH: 4,
    Severity.MEDIUM: 3,
    Severity.LOW: 2,
    Severity.INFO: 1,
}


class ScopeType(str, Enum):
    CIDR = "cidr"
    IP = "ip"
    HOST = "host"
    DOMAIN = "domain"
    URL = "url"


class ScopeEnvironment(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    CLOUD = "cloud"
    UNKNOWN = "unknown"


class AuditType(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    MIXED = "mixed"


class MissionStatus(str, Enum):
    DRAFT = "draft"
    SCOPE_DEFINED = "scope_defined"
    AUTHORIZED = "authorized"
    READY_TO_SCAN = "ready_to_scan"
    RUNNING = "running"
    REVIEW = "review"
    REPORT_READY = "report_ready"
    REMEDIATION = "remediation"
    COUNTER_TEST = "counter_test"
    CLOSED = "closed"


class FindingStatus(str, Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED_RISK = "accepted_risk"
    REMEDIATED = "remediated"
    COUNTER_TEST_PASSED = "counter_test_passed"
    COUNTER_TEST_FAILED = "counter_test_failed"


class ReportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class Contact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    role: str | None = None
    email: str | None = None
    phone: str | None = None


class Client(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("client"))
    name: str
    internal_reference: str | None = None
    contacts: list[Contact] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("name")
    @classmethod
    def require_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("client name is required")
        return value


class ScopeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("scope"))
    type: ScopeType
    value: str
    environment: ScopeEnvironment = ScopeEnvironment.UNKNOWN
    approved: bool = False
    excluded: bool = False
    notes: str | None = None

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("scope value is required")
        return value

    @model_validator(mode="after")
    def validate_scope(self) -> ScopeItem:
        if self.approved and self.excluded:
            raise ValueError("scope item cannot be both approved and excluded")
        if self.type == ScopeType.CIDR:
            ip_network(self.value, strict=False)
        elif self.type == ScopeType.IP:
            ip_address(self.value)
        elif self.type == ScopeType.URL and not self.value.startswith(("http://", "https://")):
            raise ValueError("url scope items must start with http:// or https://")
        return self


class Mission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("mission"))
    client_id: str
    name: str
    audit_type: AuditType = AuditType.MIXED
    authorization_reference: str | None = None
    status: MissionStatus = MissionStatus.DRAFT
    scope: list[ScopeItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    notes: str | None = None

    @property
    def has_approved_scope(self) -> bool:
        return any(item.approved and not item.excluded for item in self.scope)

    @property
    def is_authorized(self) -> bool:
        return bool(self.authorization_reference)


class Asset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("asset"))
    identifier: str
    asset_type: str
    display_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("finding"))
    title: str
    severity: Severity
    affected_asset: str
    category: str
    source_module: str
    proof: str
    risk: str
    remediation: str
    counter_test: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: FindingStatus = FindingStatus.NEW
    sources: list[str] = Field(default_factory=list)
    first_seen: datetime = Field(default_factory=utc_now)
    last_seen: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "title",
        "affected_asset",
        "category",
        "source_module",
        "proof",
        "risk",
        "remediation",
        "counter_test",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("finding text fields cannot be empty")
        return value

    @model_validator(mode="after")
    def ensure_source_list(self) -> Finding:
        if self.source_module not in self.sources:
            self.sources.append(self.source_module)
        return self

    @property
    def fingerprint(self) -> str:
        stable_parts = [
            self.title.lower().strip(),
            self.affected_asset.lower().strip(),
            self.category.lower().strip(),
        ]
        return sha256("|".join(stable_parts).encode("utf-8")).hexdigest()


class Report(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("report"))
    mission_id: str
    format: ReportFormat
    generated_at: datetime = Field(default_factory=utc_now)
    finding_count: int
    output_path: str | None = None


class ActivityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("event"))
    mission_id: str
    action: str
    summary: str
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("mission_id", "action", "summary")
    @classmethod
    def require_activity_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("activity event text fields cannot be empty")
        return value
