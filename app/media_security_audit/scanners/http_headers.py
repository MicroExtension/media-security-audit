"""HTTP security header audit adapter."""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

from media_security_audit.models import Finding, ScopeItem, ScopeType, Severity


HttpFetcher = Callable[[str], "HttpHeaderResponse"]
MIN_HSTS_MAX_AGE_SECONDS = 15552000


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

    parsed_url = urlparse(response.url)
    hsts_header = headers.get("strict-transport-security", "")
    if parsed_url.scheme == "https":
        if not hsts_header:
            findings.append(
                _finding(
                    response,
                    title="Missing HTTP Strict Transport Security header",
                    severity=Severity.MEDIUM,
                    proof="Strict-Transport-Security header was not present.",
                    risk="Browsers may allow protocol downgrade attempts for this site.",
                    remediation=(
                        "Enable Strict-Transport-Security on HTTPS responses after confirming "
                        "the site and expected subdomains are consistently available over HTTPS."
                    ),
                    counter_test=(
                        "Repeat the HTTP header audit and confirm Strict-Transport-Security "
                        "is present with an approved max-age."
                    ),
                    metadata={"header": "strict-transport-security", "observed": "missing"},
                )
            )
        else:
            max_age = parse_hsts_max_age(hsts_header)
            if max_age is None or max_age < MIN_HSTS_MAX_AGE_SECONDS:
                findings.append(
                    _finding(
                        response,
                        title="HTTP Strict Transport Security max-age is too low",
                        severity=Severity.LOW,
                        proof=f"Strict-Transport-Security header value: {hsts_header}",
                        risk="Short HSTS duration reduces browser-side downgrade protection.",
                        remediation=(
                            "Increase HSTS max-age to at least 15552000 seconds once HTTPS "
                            "coverage has been validated for the site."
                        ),
                        counter_test=(
                            "Repeat the HTTP header audit and confirm the HSTS max-age meets "
                            "the approved baseline."
                        ),
                        metadata={
                            "header": "strict-transport-security",
                            "observed": hsts_header,
                            "minimum_max_age": str(MIN_HSTS_MAX_AGE_SECONDS),
                        },
                    )
                )
    elif parsed_url.scheme == "http":
        findings.append(
            _finding(
                response,
                title="HTTP endpoint is not protected by HTTPS",
                severity=Severity.MEDIUM,
                proof=f"Approved URL was requested over clear-text HTTP: {response.url}",
                risk="Credentials, cookies, or sensitive pages may be exposed if users access the site over HTTP.",
                remediation="Redirect HTTP to HTTPS and verify that the HTTPS endpoint uses valid TLS.",
                counter_test="Repeat the audit with the approved URL and confirm it redirects to HTTPS.",
                metadata={"scheme": "http"},
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
                metadata={"header": "x-content-type-options", "expected": "nosniff"},
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
                metadata={"headers": "x-frame-options, content-security-policy frame-ancestors"},
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
                metadata={"header": "content-security-policy", "observed": "missing"},
            )
        )
    elif content_security_policy_is_permissive(content_security_policy):
        findings.append(
            _finding(
                response,
                title="Content-Security-Policy appears permissive",
                severity=Severity.LOW,
                proof=f"Content-Security-Policy header value: {content_security_policy}",
                risk="A permissive CSP may reduce browser-side protection against injection impact.",
                remediation=(
                    "Review the CSP and remove broad wildcards or unsafe inline allowances where "
                    "the application can support a stricter policy."
                ),
                counter_test="Repeat the HTTP header audit and confirm the CSP matches the approved baseline.",
                metadata={"header": "content-security-policy", "observed": content_security_policy},
            )
        )

    if "referrer-policy" not in headers:
        findings.append(
            _finding(
                response,
                title="Missing Referrer-Policy header",
                severity=Severity.LOW,
                proof="Referrer-Policy header was not present.",
                risk="Browsers may send more URL context to third-party sites than intended.",
                remediation="Set a Referrer-Policy such as strict-origin-when-cross-origin or no-referrer.",
                counter_test="Repeat the HTTP header audit and confirm Referrer-Policy is present.",
                metadata={"header": "referrer-policy", "observed": "missing"},
            )
        )

    if "permissions-policy" not in headers:
        findings.append(
            _finding(
                response,
                title="Missing Permissions-Policy header",
                severity=Severity.INFO,
                proof="Permissions-Policy header was not present.",
                risk="Browsers may leave powerful features available to pages that do not need them.",
                remediation=(
                    "Define a Permissions-Policy baseline for features such as camera, microphone, "
                    "geolocation, and fullscreen according to the application need."
                ),
                counter_test="Repeat the HTTP header audit and confirm Permissions-Policy is present.",
                metadata={"header": "permissions-policy", "observed": "missing"},
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
                metadata={"header": "server", "observed": server_header},
            )
        )

    return findings


def normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {key.lower(): value.strip() for key, value in headers.items()}


def parse_hsts_max_age(header_value: str) -> int | None:
    for directive in header_value.split(";"):
        name, _, value = directive.strip().partition("=")
        if name.lower() == "max-age":
            try:
                return int(value)
            except ValueError:
                return None
    return None


def content_security_policy_is_permissive(header_value: str) -> bool:
    normalized = " ".join(header_value.lower().split())
    permissive_tokens = (
        "default-src *",
        "script-src *",
        "object-src *",
        "'unsafe-inline'",
        "'unsafe-eval'",
    )
    return any(token in normalized for token in permissive_tokens)


def http_header_evidence(response: HttpHeaderResponse) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "url": response.url,
        "status_code": response.status_code,
        "method": response.method,
        "headers": dict(sorted(response.headers.items())),
    }


def _finding(
    response: HttpHeaderResponse,
    title: str,
    severity: Severity,
    proof: str,
    risk: str,
    remediation: str,
    counter_test: str,
    metadata: dict[str, str] | None = None,
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
        metadata={
            "http_status": str(response.status_code),
            "http_method": response.method,
            **(metadata or {}),
        },
    )

