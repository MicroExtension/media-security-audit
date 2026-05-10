"""View helpers for the remediation library page."""

from __future__ import annotations

from dataclasses import dataclass

from media_security_audit.remediation_library import (
    RemediationEntry,
    filter_remediations,
    remediation_categories,
)


@dataclass(frozen=True)
class RemediationLibraryView:
    entries: list[RemediationEntry]
    categories: list[str]
    selected_category: str
    query: str
    total_count: int


def build_remediation_library_view(
    query: str | None = None,
    category: str | None = None,
) -> RemediationLibraryView:
    selected_category = (category or "").strip()
    query_text = (query or "").strip()
    entries = filter_remediations(query=query_text, category=selected_category)
    return RemediationLibraryView(
        entries=entries,
        categories=remediation_categories(),
        selected_category=selected_category,
        query=query_text,
        total_count=len(entries),
    )
