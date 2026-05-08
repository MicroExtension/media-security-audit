"""Finding normalization and deduplication."""

from __future__ import annotations

from collections.abc import Iterable

from media_security_audit.models import Finding, SEVERITY_RANK


class FindingEngine:
    """Collect and deduplicate normalized findings."""

    def __init__(self) -> None:
        self._findings_by_fingerprint: dict[str, Finding] = {}

    def add(self, finding: Finding) -> Finding:
        fingerprint = finding.fingerprint
        existing = self._findings_by_fingerprint.get(fingerprint)
        if existing is None:
            self._findings_by_fingerprint[fingerprint] = finding
            return finding

        self._merge(existing, finding)
        return existing

    def add_many(self, findings: Iterable[Finding]) -> list[Finding]:
        return [self.add(finding) for finding in findings]

    def list(self) -> list[Finding]:
        return sorted(
            self._findings_by_fingerprint.values(),
            key=lambda finding: (
                -SEVERITY_RANK[finding.severity],
                finding.affected_asset,
                finding.title,
            ),
        )

    def _merge(self, existing: Finding, incoming: Finding) -> None:
        if SEVERITY_RANK[incoming.severity] > SEVERITY_RANK[existing.severity]:
            existing.severity = incoming.severity

        if incoming.confidence > existing.confidence:
            existing.confidence = incoming.confidence

        for source in incoming.sources:
            if source not in existing.sources:
                existing.sources.append(source)

        if incoming.source_module not in existing.sources:
            existing.sources.append(incoming.source_module)

        if incoming.proof not in existing.proof:
            existing.proof = f"{existing.proof}\n\nAdditional evidence:\n{incoming.proof}"

        existing.last_seen = max(existing.last_seen, incoming.last_seen)


def deduplicate_findings(findings: Iterable[Finding]) -> list[Finding]:
    engine = FindingEngine()
    engine.add_many(findings)
    return engine.list()

