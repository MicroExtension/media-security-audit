"""HTTP security header audit adapter."""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Mapping
from urllib.parse import urlparse

from media_security_audit.models import Finding, ScopeItem, ScopeType, Severity


HttpFetcher = Callable[[str], "HttpHeaderResponse"]


@dataclass(frozen=True)
class HttpHeaderResponse:
    url: str
    status_code: int
    headers: Mapping[str, str]
    method: str = "HEAD"


class HttpHeaderFetcher:
    """Fetch HTTP headers with conservative request behavior."""

    def __init__(self, timeout_seconds: int = 10, user_agent: str = "MEDIA-Security-Audit/0.1") -> None:
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def fetch(self, url: str) -> HttpHeaderResponse:
        validate_http_url(url)
        try:
            return self._request(url, method="HEAD")
        except urllib.error.HTTPError as error:
            if error.code not in {405, 501}:
                return HttpHeaderResponse(
                    url=url,
                    status_code=error.code,
                    headers=dict(error.headers.items()),
                    method="HEAD",
                )
        return self._request(url, method="GET")

    def _request(self, url: str, method: str) -> HttpHeaderResponse:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return HttpHeaderResponse(
                url=response.geturl(),
                status_code=response.status,
                headers=dict(response.headers.items()),
                method=method,
            )


def approved_http_targets(scope: list[ScopeItem]) -> list[str]:
    targets = []
    for item in scope:
        if item.approved and not item.excluded and item.type == ScopeType.URL:
            validate_http_url(item.value)
            targets.append(item.value)
    return targets


def validate_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("HTTP audit targets must start with http:// or https://")
    if not parsed.netloc:
        raise ValueError("HTTP audit target must include a host")
    if parsed.username or parsed.password:
        raise ValueError("HTTP audit target must not include credentials")
    if any(character.isspace() for character in url):
        raise ValueError("HTTP audit target cannot contain whitespace")


def audit_http_headers(response: HttpHeaderResponse) -> list[Finding]:
    headers = normalize_headers(response.headers)
    findings = []

    if response.url.startswith("https://") and "strict-transport-security" not in headers:
        findings.append(
            _finding(
                response,
                title="Missing HTTP Strict Transport Security header",
                severity=Severity.MEDIUM,
                proof="Strict-Transport-Security header was not present.",
                risk="Browsers may allow protocol downgrade attempts for this site.",
                remediation="Enable Strict-Transport-Security with an appropriate max-age.",
                counter_test="Repeat the HTTP header audit and confirm Strict-Transport-Security is present.",
            )
        )

    if headers.get("x-content-type-options", "").lower() != "nosniff":
        findings.append(
            _finding(
                response,
                title="Missing X-Content-Type-Options nosniff header",
                severity=Severity.LOW,
                proof="X-Content-Type-Options header was missing or not set to nosniff.",
                risk="Browsers may attempt MIME sniffing on responses.",
                remediation="Set X-Content-Type-Options to nosniff.",
                counter_test="Repeat the HTTP header audit and confirm X-Content-Type-Options: nosniff.",
            )
        )

    content_security_policy = headers.get("content-security-policy", "")
    x_frame_options = headers.get("x-frame-options", "")
    if "frame-ancestors" not in content_security_policy.lower() and not x_frame_options:
        findings.append(
            _finding(
                response,
                title="Missing clickjacking protection header",
                severity=Severity.MEDIUM,
                proof="Neither X-Frame-Options nor CSP frame-ancestors was present.",
                risk="Pages may be embedded in hostile frames if the application is vulnerable to clickjacking.",
                remediation="Set X-Frame-Options or a Content-Security-Policy frame-ancestors directive.",
                counter_test="Repeat the HTTP header audit and confirm frame embedding is restricted.",
            )
        )

    if "content-security-policy" not in headers:
        findings.append(
            _finding(
                response,
                title="Missing Content-Security-Policy header",
                severity=Severity.LOW,
                proof="Content-Security-Policy header was not present.",
                risk="Browser-side injection impact may be higher without a CSP baseline.",
                remediation="Define a Content-Security-Policy appropriate for the application.",
                counter_test="Repeat the HTTP header audit and confirm Content-Security-Policy is present.",
            )
        )

    server_header = headers.get("server")
    if server_header:
        findings.append(
            _finding(
                response,
                title="Server header exposes platform information",
                severity=Severity.INFO,
                proof=f"Server header value: {server_header}",
                risk="Technology disclosure can help attackers tailor reconnaissance.",
                remediation="Reduce Server header detail where supported by the web server or reverse proxy.",
                counter_test="Repeat the HTTP header audit and confirm the Server header is absent or generic.",
            )
        )

    return findings


def normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {key.lower(): value.strip() for key, value in headers.items()}


def _finding(
    response: HttpHeaderResponse,
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
        affected_asset=response.url,
        category="http_headers",
        source_module="http_headers",
        proof=f"{proof} HTTP status: {response.status_code}. Method: {response.method}.",
        risk=risk,
        remediation=remediation,
        counter_test=counter_test,
        confidence=0.85,
    )

