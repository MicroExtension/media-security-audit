"""Guarded testssl.sh adapter and JSON parser."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from media_security_audit.models import Finding, ScopeItem, ScopeType, Severity
from media_security_audit.scanners.nmap import render_command


TLS_TARGET_TYPES = {
    ScopeType.IP,
    ScopeType.HOST,
    ScopeType.DOMAIN,
    ScopeType.URL,
}

SEVERITY_MAP = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
    "WARN": Severity.LOW,
}


@dataclass(frozen=True)
class TestsslExecutionResult:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    output_path: Path | None
    target: str


TestsslRunner = Callable[[list[str], int], subprocess.CompletedProcess[str]]
ExecutableLookup = Callable[[str], str | None]


class TestsslCommandBuilder:
    """Build conservative testssl.sh commands without invoking a shell."""

    def __init__(self, executable: str = "testssl.sh") -> None:
        self.executable = executable

    def build(self, target: str, output_path: Path | None = None) -> list[str]:
        normalized_target = validate_tls_target(target)
        command = [
            self.executable,
            "--warnings",
            "batch",
            "--severity",
            "MEDIUM",
        ]
        if output_path is not None:
            command.extend(["--jsonfile-pretty", str(output_path)])
        command.append(normalized_target)
        return command

    def build_for_scope(
        self,
        scope: list[ScopeItem],
        output_dir: Path | None = None,
    ) -> list[list[str]]:
        targets = approved_tls_targets(scope)
        commands = []
        for index, target in enumerate(targets, start=1):
            output_path = output_dir / f"testssl-{index}.json" if output_dir else None
            commands.append(self.build(target, output_path=output_path))
        return commands


class TestsslExecutor:
    """Execute pre-built testssl.sh commands with guardrails."""

    def __init__(
        self,
        runner: TestsslRunner | None = None,
        executable_lookup: ExecutableLookup = shutil.which,
        timeout_seconds: int = 900,
    ) -> None:
        self.runner = runner or self._default_runner
        self.executable_lookup = executable_lookup
        self.timeout_seconds = timeout_seconds

    def run(self, command: list[str]) -> TestsslExecutionResult:
        validate_testssl_command(command)
        executable = command[0]
        if self.executable_lookup(executable) is None:
            raise FileNotFoundError(f"testssl.sh executable not found: {executable}")

        output_path = testssl_output_path(command)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        completed = self.runner(command, self.timeout_seconds)
        return TestsslExecutionResult(
            command=tuple(command),
            exit_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            output_path=output_path,
            target=command[-1],
        )

    @staticmethod
    def _default_runner(
        command: list[str],
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )


def approved_tls_targets(scope: list[ScopeItem]) -> list[str]:
    targets = []
    seen = set()
    for item in scope:
        if item.approved and not item.excluded and item.type in TLS_TARGET_TYPES:
            target = tls_target_from_scope_item(item)
            if target not in seen:
                targets.append(target)
                seen.add(target)
    return targets


def tls_target_from_scope_item(item: ScopeItem) -> str:
    if item.type == ScopeType.URL:
        return tls_target_from_url(item.value)
    return validate_tls_target(item.value)


def tls_target_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("TLS audit URL targets must start with https://")
    if not parsed.netloc:
        raise ValueError("TLS audit URL target must include a host")
    if parsed.username or parsed.password:
        raise ValueError("TLS audit URL target must not include credentials")
    return validate_tls_target(parsed.netloc)


def validate_tls_target(target: str) -> str:
    value = target.strip()
    if not value:
        raise ValueError("TLS audit target is required")
    if value.startswith("-"):
        raise ValueError("TLS audit target cannot start with '-'")
    if any(character.isspace() for character in value):
        raise ValueError("TLS audit target cannot contain whitespace")
    if "://" in value or "/" in value or "@" in value:
        raise ValueError("TLS audit target must be a bare host, IP, or host:port")
    return value.lower()


def validate_testssl_command(command: list[str]) -> None:
    if not command:
        raise ValueError("testssl.sh command cannot be empty")
    if command[0].startswith("-"):
        raise ValueError("testssl.sh executable cannot start with '-'")
    if "--parallel" in command:
        raise ValueError("parallel testssl.sh mode is not allowed")
    if "--openssl" in command:
        raise ValueError("custom OpenSSL paths are not allowed by the safe adapter")
    validate_tls_target(command[-1])


def testssl_output_path(command: list[str]) -> Path | None:
    try:
        index = command.index("--jsonfile-pretty")
    except ValueError:
        return None

    if index + 1 >= len(command):
        raise ValueError("testssl.sh command is missing the JSON output path")

    return Path(command[index + 1])


def parse_testssl_json(json_content: str, target: str) -> list[Finding]:
    data = json.loads(json_content)
    findings = []
    for item in _result_items(data):
        severity = _severity_from_item(item)
        if severity is None:
            continue
        finding_id = str(item.get("id") or item.get("testId") or "tls_check")
        finding_text = str(item.get("finding") or item.get("message") or "TLS issue reported.")
        findings.append(
            Finding(
                title=f"TLS finding: {finding_id}",
                severity=severity,
                affected_asset=validate_tls_target(target),
                category="tls",
                source_module="testssl",
                proof=f"testssl.sh reported {finding_id}: {finding_text}",
                risk=_risk_for_testssl_id(finding_id),
                remediation=_remediation_for_testssl_id(finding_id),
                counter_test=(
                    "Run the approved testssl.sh check again and confirm this item is no "
                    "longer reported with a warning severity."
                ),
                confidence=0.8,
            )
        )
    return findings


def parse_testssl_json_file(path: Path, target: str) -> list[Finding]:
    return parse_testssl_json(path.read_text(encoding="utf-8"), target)


def _result_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("scanResult", "results", "findings"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [
            item
            for value in data.values()
            if isinstance(value, list)
            for item in value
            if isinstance(item, dict)
        ]
    return []


def _severity_from_item(item: dict[str, Any]) -> Severity | None:
    raw = str(item.get("severity") or "").strip().upper()
    return SEVERITY_MAP.get(raw)


def _risk_for_testssl_id(finding_id: str) -> str:
    check = finding_id.lower()
    if "ssl" in check or "tls1" in check:
        return "Legacy TLS or SSL support can allow downgrade attacks or weak encrypted sessions."
    if "cipher" in check or "rc4" in check or "sweet32" in check:
        return "Weak cipher suites can reduce confidentiality for encrypted traffic."
    if "cert" in check or "chain" in check or "trust" in check:
        return "Certificate or trust-chain issues can break identity validation for users."
    return "TLS configuration weakness may reduce transport security for exposed services."


def _remediation_for_testssl_id(finding_id: str) -> str:
    check = finding_id.lower()
    if "ssl" in check or "tls1" in check:
        return "Disable legacy SSL/TLS protocols and keep only currently supported TLS versions."
    if "cipher" in check or "rc4" in check or "sweet32" in check:
        return "Disable weak cipher suites and prefer modern AEAD ciphers."
    if "cert" in check or "chain" in check or "trust" in check:
        return "Replace or reissue the certificate and fix the served certificate chain."
    return "Review the service TLS configuration and apply the vendor hardening guidance."


def render_testssl_command(command: list[str]) -> str:
    return render_command(command)
