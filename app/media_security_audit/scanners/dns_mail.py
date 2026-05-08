"""DNS and mail authentication audit adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from media_security_audit.models import Finding, ScopeItem, ScopeType, Severity


DnsTxtResolver = Callable[[str], list[str]]


@dataclass(frozen=True)
class DnsMailRecordSet:
    domain: str
    spf_records: tuple[str, ...]
    dmarc_records: tuple[str, ...]
    dkim_records: dict[str, tuple[str, ...]]


class DnsPythonTxtResolver:
    """TXT resolver backed by dnspython when available."""

    def __call__(self, name: str) -> list[str]:
        try:
            import dns.exception
            import dns.resolver
        except ModuleNotFoundError as error:
            raise RuntimeError("dnspython is required for live DNS lookups") from error

        try:
            answers = dns.resolver.resolve(name, "TXT")
        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):
            return []

        values = []
        for answer in answers:
            if hasattr(answer, "strings"):
                values.append("".join(_decode_txt_part(part) for part in answer.strings))
            else:
                values.append(str(answer).strip('"'))
        return values


def approved_dns_domains(scope: list[ScopeItem]) -> list[str]:
    domains = []
    for item in scope:
        if item.approved and not item.excluded and item.type == ScopeType.DOMAIN:
            domains.append(validate_domain(item.value))
    return domains


def dns_mail_query_plan(domains: list[str], dkim_selectors: list[str] | None = None) -> list[str]:
    selectors = dkim_selectors or []
    queries = []
    for domain in domains:
        normalized = validate_domain(domain)
        queries.append(f"TXT {normalized}")
        queries.append(f"TXT _dmarc.{normalized}")
        queries.extend(f"TXT {validate_selector(selector)}._domainkey.{normalized}" for selector in selectors)
    return queries


def collect_dns_mail_records(
    domain: str,
    resolver: DnsTxtResolver,
    dkim_selectors: list[str] | None = None,
) -> DnsMailRecordSet:
    normalized_domain = validate_domain(domain)
    selectors = dkim_selectors or []
    spf_records = tuple(record for record in resolver(normalized_domain) if _is_spf(record))
    dmarc_name = f"_dmarc.{normalized_domain}"
    dmarc_records = tuple(record for record in resolver(dmarc_name) if _is_dmarc(record))
    dkim_records: dict[str, tuple[str, ...]] = {}

    for selector in selectors:
        normalized_selector = validate_selector(selector)
        name = f"{normalized_selector}._domainkey.{normalized_domain}"
        dkim_records[normalized_selector] = tuple(resolver(name))

    return DnsMailRecordSet(
        domain=normalized_domain,
        spf_records=spf_records,
        dmarc_records=dmarc_records,
        dkim_records=dkim_records,
    )


def audit_dns_mail_records(records: DnsMailRecordSet) -> list[Finding]:
    findings = []
    findings.extend(_spf_findings(records))
    findings.extend(_dmarc_findings(records))
    findings.extend(_dkim_findings(records))
    return findings


def audit_dns_mail_domain(
    domain: str,
    resolver: DnsTxtResolver,
    dkim_selectors: list[str] | None = None,
) -> list[Finding]:
    return audit_dns_mail_records(collect_dns_mail_records(domain, resolver, dkim_selectors))


def validate_domain(domain: str) -> str:
    value = domain.strip().rstrip(".").lower()
    if not value:
        raise ValueError("DNS domain is required")
    if any(character.isspace() for character in value):
        raise ValueError("DNS domain cannot contain whitespace")
    if value.startswith("-"):
        raise ValueError("DNS domain cannot start with '-'")
    if "://" in value or "/" in value or "@" in value:
        raise ValueError("DNS domain must be a bare domain name")
    if "." not in value:
        raise ValueError("DNS domain must contain at least one dot")
    return value


def validate_selector(selector: str) -> str:
    value = selector.strip().lower()
    if not value:
        raise ValueError("DKIM selector cannot be empty")
    if any(character.isspace() for character in value):
        raise ValueError("DKIM selector cannot contain whitespace")
    if value.startswith("-"):
        raise ValueError("DKIM selector cannot start with '-'")
    if "." in value or "/" in value or "@" in value:
        raise ValueError("DKIM selector must be a single DNS label")
    return value


def _spf_findings(records: DnsMailRecordSet) -> list[Finding]:
    if not records.spf_records:
        return [
            _finding(
                records.domain,
                title="SPF record is missing",
                severity=Severity.MEDIUM,
                proof="No TXT record starting with v=spf1 was found at the domain root.",
                risk="Spoofed email may be harder for recipients to identify.",
                remediation="Publish a SPF TXT record that lists authorized sending systems.",
                counter_test="Query the domain TXT records and confirm exactly one v=spf1 record exists.",
            )
        ]

    findings = []
    if len(records.spf_records) > 1:
        findings.append(
            _finding(
                records.domain,
                title="Multiple SPF records are published",
                severity=Severity.MEDIUM,
                proof=f"SPF records: {' | '.join(records.spf_records)}",
                risk="Multiple SPF records can cause SPF evaluation errors.",
                remediation="Publish a single consolidated SPF TXT record.",
                counter_test="Query the domain TXT records and confirm only one v=spf1 record exists.",
            )
        )

    spf = " ".join(records.spf_records).lower()
    if "+all" in spf:
        findings.append(
            _finding(
                records.domain,
                title="SPF record permits all senders",
                severity=Severity.HIGH,
                proof=f"SPF record: {' | '.join(records.spf_records)}",
                risk="The +all mechanism allows any sender to pass SPF.",
                remediation="Replace +all with a restrictive all mechanism after validating legitimate senders.",
                counter_test="Query the SPF record and confirm +all is no longer present.",
            )
        )
    elif "-all" not in spf and "~all" not in spf:
        findings.append(
            _finding(
                records.domain,
                title="SPF record does not end with an enforcement mechanism",
                severity=Severity.LOW,
                proof=f"SPF record: {' | '.join(records.spf_records)}",
                risk="SPF policy may be too permissive or ambiguous.",
                remediation="Use ~all or -all once authorized senders are confirmed.",
                counter_test="Query the SPF record and confirm it contains ~all or -all.",
            )
        )

    return findings


def _dmarc_findings(records: DnsMailRecordSet) -> list[Finding]:
    if not records.dmarc_records:
        return [
            _finding(
                records.domain,
                title="DMARC record is missing",
                severity=Severity.MEDIUM,
                proof=f"No v=DMARC1 TXT record was found at _dmarc.{records.domain}.",
                risk="Recipients cannot apply the domain owner's DMARC policy.",
                remediation="Publish a DMARC TXT record and move toward quarantine or reject after monitoring.",
                counter_test=f"Query _dmarc.{records.domain} and confirm a v=DMARC1 record exists.",
            )
        ]

    if len(records.dmarc_records) > 1:
        return [
            _finding(
                records.domain,
                title="Multiple DMARC records are published",
                severity=Severity.MEDIUM,
                proof=f"DMARC records: {' | '.join(records.dmarc_records)}",
                risk="Multiple DMARC records can cause DMARC evaluation errors.",
                remediation="Publish a single DMARC TXT record.",
                counter_test=f"Query _dmarc.{records.domain} and confirm only one v=DMARC1 record exists.",
            )
        ]

    policy = _dmarc_policy(records.dmarc_records[0])
    if policy == "none":
        return [
            _finding(
                records.domain,
                title="DMARC policy is monitoring only",
                severity=Severity.LOW,
                proof=f"DMARC record: {records.dmarc_records[0]}",
                risk="DMARC policy does not request quarantine or rejection of failing mail.",
                remediation="Move gradually from p=none to quarantine or reject after monitoring.",
                counter_test=f"Query _dmarc.{records.domain} and confirm p=quarantine or p=reject.",
            )
        ]
    if policy not in {"quarantine", "reject"}:
        return [
            _finding(
                records.domain,
                title="DMARC policy is missing or invalid",
                severity=Severity.MEDIUM,
                proof=f"DMARC record: {records.dmarc_records[0]}",
                risk="Recipients may not be able to apply a clear DMARC policy.",
                remediation="Set a valid DMARC p=none, p=quarantine, or p=reject policy.",
                counter_test=f"Query _dmarc.{records.domain} and confirm a valid p= policy exists.",
            )
        ]
    return []


def _dkim_findings(records: DnsMailRecordSet) -> list[Finding]:
    findings = []
    for selector, values in records.dkim_records.items():
        asset = f"{selector}._domainkey.{records.domain}"
        dkim_records = [value for value in values if value.lower().startswith("v=dkim1")]
        if not dkim_records:
            findings.append(
                _finding(
                    asset,
                    title="DKIM selector TXT record is missing",
                    severity=Severity.LOW,
                    proof=f"No v=DKIM1 TXT record was found for selector {selector}.",
                    risk="Mail signed with this selector may fail DKIM verification.",
                    remediation="Publish the expected DKIM public key or remove unused selector checks.",
                    counter_test=f"Query {asset} and confirm a v=DKIM1 TXT record exists.",
                )
            )
            continue

        if any("p=" not in record.lower() or "p=;" in record.lower() for record in dkim_records):
            findings.append(
                _finding(
                    asset,
                    title="DKIM selector has no usable public key",
                    severity=Severity.MEDIUM,
                    proof=f"DKIM record: {' | '.join(dkim_records)}",
                    risk="DKIM verification may fail for mail using this selector.",
                    remediation="Publish a DKIM record with a valid public key.",
                    counter_test=f"Query {asset} and confirm the p= tag contains a public key.",
                )
            )
    return findings


def _finding(
    asset: str,
    title: str,
    severity: Severity,
    proof: str,
    risk: str,
    remediation: str,
    counter_test: str,
) -> Finding:
    return Finding(
        title=title,
        severity=severity,
        affected_asset=asset,
        category="dns_mail",
        source_module="dns_mail",
        proof=proof,
        risk=risk,
        remediation=remediation,
        counter_test=counter_test,
        confidence=0.85,
    )


def _is_spf(record: str) -> bool:
    return record.strip().lower().startswith("v=spf1")


def _is_dmarc(record: str) -> bool:
    return record.strip().lower().startswith("v=dmarc1")


def _dmarc_policy(record: str) -> str | None:
    tags = {}
    for part in record.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            tags[key.strip().lower()] = value.strip().lower()
    return tags.get("p")


def _decode_txt_part(part: object) -> str:
    if isinstance(part, bytes):
        return part.decode("utf-8", errors="replace")
    return str(part)

