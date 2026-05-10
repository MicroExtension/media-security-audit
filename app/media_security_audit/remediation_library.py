"""Built-in remediation library for common MSP audit findings."""

from __future__ import annotations

from dataclasses import dataclass

from media_security_audit.models import Severity


@dataclass(frozen=True)
class RemediationEntry:
    id: str
    title: str
    category: str
    severity: Severity
    effort: str
    applies_to: tuple[str, ...]
    risk: str
    remediation: str
    counter_test: str


BUILTIN_REMEDIATIONS: tuple[RemediationEntry, ...] = (
    RemediationEntry(
        id="rem_http_hsts",
        title="Enable HTTP Strict Transport Security",
        category="http_headers",
        severity=Severity.MEDIUM,
        effort="low",
        applies_to=("web", "reverse_proxy", "load_balancer"),
        risk="Users may be exposed to protocol downgrade attempts on hostile networks.",
        remediation=(
            "Enable the Strict-Transport-Security header on HTTPS responses after "
            "confirming the site and subdomains are consistently served over HTTPS."
        ),
        counter_test="Request the approved URL and confirm the Strict-Transport-Security header is present.",
    ),
    RemediationEntry(
        id="rem_http_clickjacking",
        title="Protect Web Interfaces Against Clickjacking",
        category="http_headers",
        severity=Severity.LOW,
        effort="low",
        applies_to=("web", "admin_portal"),
        risk="Sensitive interfaces may be framed by another site and abused in social engineering flows.",
        remediation=(
            "Set an appropriate Content-Security-Policy frame-ancestors directive "
            "or X-Frame-Options header for administrative interfaces."
        ),
        counter_test="Request the approved URL and confirm a frame-ancestors or X-Frame-Options policy is returned.",
    ),
    RemediationEntry(
        id="rem_dmarc_enforcement",
        title="Move DMARC Toward Enforcement",
        category="dns_mail",
        severity=Severity.LOW,
        effort="medium",
        applies_to=("mail", "dns"),
        risk="Spoofed emails may be harder for recipients to reject automatically.",
        remediation=(
            "Publish or tighten the DMARC record, monitor aggregate reports, then "
            "move progressively from p=none to quarantine or reject."
        ),
        counter_test="Query _dmarc.<domain> and confirm the expected DMARC policy is published.",
    ),
    RemediationEntry(
        id="rem_spf_overly_permissive",
        title="Reduce Overly Permissive SPF Records",
        category="dns_mail",
        severity=Severity.MEDIUM,
        effort="medium",
        applies_to=("mail", "dns"),
        risk="Overly permissive SPF records can allow unauthorized mail sources to pass SPF checks.",
        remediation=(
            "Replace broad mechanisms such as +all with explicit authorized senders, "
            "then use a restrictive all mechanism such as -all or ~all."
        ),
        counter_test="Query the domain TXT records and confirm SPF no longer authorizes arbitrary senders.",
    ),
    RemediationEntry(
        id="rem_rdp_restrict_exposure",
        title="Restrict RDP Exposure",
        category="network",
        severity=Severity.HIGH,
        effort="medium",
        applies_to=("windows", "firewall", "vpn"),
        risk="Remote administration exposed beyond trusted networks increases compromise risk.",
        remediation=(
            "Restrict RDP to VPN or trusted administrative networks, enforce MFA on "
            "remote access, and review firewall rules for public or broad internal exposure."
        ),
        counter_test="Repeat the approved service scan and confirm RDP is reachable only from approved sources.",
    ),
    RemediationEntry(
        id="rem_smb_signing",
        title="Require SMB Signing Where Appropriate",
        category="smb",
        severity=Severity.MEDIUM,
        effort="medium",
        applies_to=("windows", "active_directory", "file_server"),
        risk="Unsigned SMB traffic may be vulnerable to relay or tampering in some network positions.",
        remediation=(
            "Require SMB signing on servers that support it, validate legacy system "
            "compatibility, and roll out policy changes in controlled phases."
        ),
        counter_test="Repeat the approved SMB audit and confirm signing is required on target servers.",
    ),
    RemediationEntry(
        id="rem_smbv1_disable",
        title="Disable SMBv1",
        category="smb",
        severity=Severity.HIGH,
        effort="medium",
        applies_to=("windows", "nas", "file_server"),
        risk="SMBv1 is obsolete and materially increases exposure to known attack techniques.",
        remediation=(
            "Inventory legacy dependencies, disable SMBv1 on clients and servers, "
            "and replace devices or applications that still require it."
        ),
        counter_test="Repeat the approved SMB audit and confirm SMBv1 is not negotiated.",
    ),
    RemediationEntry(
        id="rem_tls_legacy_protocols",
        title="Disable Legacy TLS Protocols",
        category="tls",
        severity=Severity.MEDIUM,
        effort="medium",
        applies_to=("web", "vpn", "mail_gateway", "firewall"),
        risk="Legacy TLS protocols can expose services to downgrade or cryptographic weaknesses.",
        remediation=(
            "Disable SSLv3, TLS 1.0, and TLS 1.1 where supported, then validate "
            "client compatibility before enforcing the change broadly."
        ),
        counter_test="Repeat the approved TLS test and confirm only accepted protocol versions are offered.",
    ),
)


def list_remediations() -> list[RemediationEntry]:
    return sorted(BUILTIN_REMEDIATIONS, key=lambda entry: (entry.category, entry.title))


def remediation_categories() -> list[str]:
    return sorted({entry.category for entry in BUILTIN_REMEDIATIONS})


def filter_remediations(
    query: str | None = None,
    category: str | None = None,
) -> list[RemediationEntry]:
    query_text = (query or "").strip().lower()
    category_text = (category or "").strip()
    entries = list_remediations()
    if category_text:
        entries = [entry for entry in entries if entry.category == category_text]
    if query_text:
        entries = [
            entry
            for entry in entries
            if query_text in searchable_text(entry)
        ]
    return entries


def searchable_text(entry: RemediationEntry) -> str:
    parts = (
        entry.id,
        entry.title,
        entry.category,
        entry.severity.value,
        entry.effort,
        " ".join(entry.applies_to),
        entry.risk,
        entry.remediation,
        entry.counter_test,
    )
    return " ".join(parts).lower()
