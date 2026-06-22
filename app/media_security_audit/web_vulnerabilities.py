"""Web view models for the vulnerability catalog workspace."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from media_security_audit.models import Severity, VulnerabilityAdvisory
from media_security_audit.vulnerability_catalog import (
    CISA_KEV_URL,
    VulnerabilityCatalogDocument,
    load_vulnerability_catalog,
)


@dataclass(frozen=True)
class VulnerabilityCatalogSummary:
    source: str
    advisory_count: int
    known_exploited_count: int
    critical_or_high_count: int
    latest_update: str
    update_source: str
    status: str
    detail: str


@dataclass(frozen=True)
class VulnerabilityCatalogSeverityRow:
    severity: str
    label: str
    count: int


@dataclass(frozen=True)
class VulnerabilityCatalogRow:
    cve_id: str
    title: str
    severity: str
    known_exploited: bool
    affected_products: str
    affected_versions: str
    remediation: str
    counter_test: str
    source: str
    updated_at: str
    references: tuple[str, ...]


@dataclass(frozen=True)
class VulnerabilityCatalogView:
    summary: VulnerabilityCatalogSummary
    severity_rows: list[VulnerabilityCatalogSeverityRow]
    rows: list[VulnerabilityCatalogRow]


def build_vulnerability_catalog_view(data_dir: Path) -> VulnerabilityCatalogView:
    catalog = load_vulnerability_catalog(data_dir)
    rows = [vulnerability_catalog_row(advisory) for advisory in catalog.advisories]
    return VulnerabilityCatalogView(
        summary=vulnerability_catalog_summary(catalog),
        severity_rows=vulnerability_catalog_severity_rows(catalog),
        rows=rows,
    )


def vulnerability_catalog_summary(
    catalog: VulnerabilityCatalogDocument,
) -> VulnerabilityCatalogSummary:
    latest_update = latest_catalog_update(catalog.advisories)
    known_exploited_count = len([item for item in catalog.advisories if item.known_exploited])
    critical_or_high_count = len(
        [
            item
            for item in catalog.advisories
            if item.severity in {Severity.CRITICAL, Severity.HIGH}
        ]
    )
    if not catalog.advisories:
        status = "missing"
        detail = "No CVE/KEV catalog has been imported yet."
    elif known_exploited_count:
        status = "warning"
        detail = f"{known_exploited_count} known exploited item(s) are available for correlation."
    else:
        status = "ready"
        detail = "Catalog is ready for mission correlation."
    return VulnerabilityCatalogSummary(
        source=catalog.source,
        advisory_count=len(catalog.advisories),
        known_exploited_count=known_exploited_count,
        critical_or_high_count=critical_or_high_count,
        latest_update=latest_update.isoformat() if latest_update else "not available",
        update_source=CISA_KEV_URL,
        status=status,
        detail=detail,
    )


def vulnerability_catalog_severity_rows(
    catalog: VulnerabilityCatalogDocument,
) -> list[VulnerabilityCatalogSeverityRow]:
    counts = {severity: 0 for severity in Severity}
    for advisory in catalog.advisories:
        counts[advisory.severity] += 1
    return [
        VulnerabilityCatalogSeverityRow(
            severity=severity.value,
            label=severity.value.replace("_", " ").title(),
            count=counts[severity],
        )
        for severity in Severity
    ]


def vulnerability_catalog_row(advisory: VulnerabilityAdvisory) -> VulnerabilityCatalogRow:
    return VulnerabilityCatalogRow(
        cve_id=advisory.cve_id,
        title=advisory.title,
        severity=advisory.severity.value,
        known_exploited=advisory.known_exploited,
        affected_products=", ".join(advisory.affected_products) or "unspecified",
        affected_versions=", ".join(advisory.affected_versions) or "any detected version",
        remediation=advisory.remediation,
        counter_test=advisory.counter_test,
        source=advisory.source,
        updated_at=advisory.updated_at.isoformat()
        if advisory.updated_at
        else advisory.published_at.isoformat()
        if advisory.published_at
        else "not available",
        references=tuple(advisory.references),
    )


def latest_catalog_update(advisories: list[VulnerabilityAdvisory]) -> date | None:
    values = [
        value
        for advisory in advisories
        for value in [advisory.updated_at, advisory.published_at]
        if value is not None
    ]
    return max(values) if values else None
