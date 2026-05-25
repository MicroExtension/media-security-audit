"""Guarded ldapsearch RootDSE adapter and LDIF parser."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable

from media_security_audit.models import Finding, ScopeItem, ScopeType, Severity
from media_security_audit.scanners.nmap import render_command


LDAP_TARGET_TYPES = {
    ScopeType.IP,
    ScopeType.HOST,
    ScopeType.DOMAIN,
}


@dataclass(frozen=True)
class LdapRootDse:
    target: str
    naming_contexts: tuple[str, ...]
    supported_ldap_versions: tuple[str, ...]
    supported_sasl_mechanisms: tuple[str, ...]


@dataclass(frozen=True)
class LdapExecutionResult:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    target: str


LdapRunner = Callable[[list[str], int], subprocess.CompletedProcess[str]]
ExecutableLookup = Callable[[str], str | None]


class LdapCommandBuilder:
    """Build conservative anonymous RootDSE ldapsearch commands."""

    def __init__(self, executable: str = "ldapsearch") -> None:
        self.executable = executable

    def build(self, target: str) -> list[str]:
        normalized_target = validate_ldap_target(target)
        return [
            self.executable,
            "-x",
            "-LLL",
            "-H",
            f"ldap://{normalized_target}",
            "-s",
            "base",
            "-b",
            "",
            "-o",
            "nettimeout=10",
            "namingContexts",
            "supportedLDAPVersion",
            "supportedSASLMechanisms",
        ]

    def build_for_scope(self, scope: list[ScopeItem]) -> list[list[str]]:
        return [self.build(target) for target in approved_ldap_targets(scope)]


class LdapExecutor:
    """Execute pre-built ldapsearch commands with guardrails."""

    def __init__(
        self,
        runner: LdapRunner | None = None,
        executable_lookup: ExecutableLookup = shutil.which,
        timeout_seconds: int = 60,
    ) -> None:
        self.runner = runner or self._default_runner
        self.executable_lookup = executable_lookup
        self.timeout_seconds = timeout_seconds

    def run(self, command: list[str]) -> LdapExecutionResult:
        validate_ldap_command(command)
        executable = command[0]
        if self.executable_lookup(executable) is None:
            raise FileNotFoundError(f"ldapsearch executable not found: {executable}")

        completed = self.runner(command, self.timeout_seconds)
        return LdapExecutionResult(
            command=tuple(command),
            exit_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            target=ldap_target_from_command(command),
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


def approved_ldap_targets(scope: list[ScopeItem]) -> list[str]:
    targets = []
    seen = set()
    for item in scope:
        if item.approved and not item.excluded and item.type in LDAP_TARGET_TYPES:
            target = validate_ldap_target(item.value)
            if target not in seen:
                targets.append(target)
                seen.add(target)
    return targets


def validate_ldap_target(target: str) -> str:
    value = target.strip()
    if not value:
        raise ValueError("LDAP audit target is required")
    if value.startswith("-"):
        raise ValueError("LDAP audit target cannot start with '-'")
    if any(character.isspace() for character in value):
        raise ValueError("LDAP audit target cannot contain whitespace")
    if "://" in value or "/" in value or "\\" in value or "@" in value:
        raise ValueError("LDAP audit target must be a bare host, IP, or domain")
    return value.lower()


def validate_ldap_command(command: list[str]) -> None:
    if not command:
        raise ValueError("ldapsearch command cannot be empty")
    if command[0].startswith("-"):
        raise ValueError("ldapsearch executable cannot start with '-'")

    credential_flags = {"-D", "-w", "-W", "-y", "-Y", "-U", "--bindDN"}
    if any(flag in command for flag in credential_flags):
        raise ValueError("credentialed LDAP checks are not allowed by the basic adapter")
    if "-f" in command:
        raise ValueError("file-driven LDAP searches are not allowed")
    if "-e" in command or "-E" in command:
        raise ValueError("LDAP controls and extensions are not allowed by the basic adapter")
    if _option_value(command, "-s") != "base":
        raise ValueError("LDAP basic adapter only allows base-scope RootDSE searches")
    if _option_value(command, "-b") != "":
        raise ValueError("LDAP basic adapter only allows empty RootDSE base DN")
    ldap_target_from_command(command)


def ldap_target_from_command(command: list[str]) -> str:
    try:
        index = command.index("-H")
    except ValueError as error:
        raise ValueError("ldapsearch command must include -H") from error
    if index + 1 >= len(command):
        raise ValueError("ldapsearch command is missing the -H URI")
    uri = command[index + 1]
    if not uri.startswith("ldap://"):
        raise ValueError("LDAP basic adapter only allows ldap:// URIs")
    return validate_ldap_target(uri.removeprefix("ldap://"))


def _option_value(command: list[str], option: str) -> str | None:
    try:
        index = command.index(option)
    except ValueError:
        return None
    if index + 1 >= len(command):
        return None
    return command[index + 1]


def parse_ldap_root_dse(output: str, target: str) -> LdapRootDse:
    attributes = _parse_ldif_attributes(output)
    return LdapRootDse(
        target=validate_ldap_target(target),
        naming_contexts=tuple(attributes.get("namingcontexts", [])),
        supported_ldap_versions=tuple(attributes.get("supportedldapversion", [])),
        supported_sasl_mechanisms=tuple(attributes.get("supportedsaslmechanisms", [])),
    )


def findings_from_root_dse(root_dse: LdapRootDse) -> list[Finding]:
    findings = []
    if "2" in root_dse.supported_ldap_versions:
        findings.append(
            Finding(
                title="LDAPv2 is advertised by directory service",
                severity=Severity.MEDIUM,
                affected_asset=root_dse.target,
                category="ldap",
                source_module="ldapsearch",
                proof=(
                    "supportedLDAPVersion includes: "
                    f"{', '.join(root_dse.supported_ldap_versions)}."
                ),
                risk="LDAPv2 is obsolete and may indicate legacy directory compatibility exposure.",
                remediation=(
                    "Disable LDAPv2 support where possible and require modern LDAP "
                    "protocol handling."
                ),
                counter_test=(
                    "Run the approved LDAP RootDSE check again and confirm supportedLDAPVersion "
                    "does not include 2."
                ),
                confidence=0.8,
            )
        )

    sasl_values = {item.upper() for item in root_dse.supported_sasl_mechanisms}
    if "ANONYMOUS" in sasl_values:
        findings.append(
            Finding(
                title="LDAP advertises anonymous SASL mechanism",
                severity=Severity.MEDIUM,
                affected_asset=root_dse.target,
                category="ldap",
                source_module="ldapsearch",
                proof=(
                    "supportedSASLMechanisms includes: "
                    f"{', '.join(root_dse.supported_sasl_mechanisms)}."
                ),
                risk="Anonymous LDAP mechanisms can expose directory metadata without attribution.",
                remediation=(
                    "Disable anonymous LDAP mechanisms unless a documented dependency "
                    "requires them."
                ),
                counter_test=(
                    "Run the approved LDAP RootDSE check again and confirm ANONYMOUS is not "
                    "listed in supportedSASLMechanisms."
                ),
                confidence=0.8,
            )
        )

    if root_dse.naming_contexts:
        findings.append(
            Finding(
                title="LDAP RootDSE exposes naming contexts",
                severity=Severity.INFO,
                affected_asset=root_dse.target,
                category="ldap",
                source_module="ldapsearch",
                proof=f"namingContexts: {', '.join(root_dse.naming_contexts)}.",
                risk=(
                    "RootDSE metadata can help technicians and attackers identify directory "
                    "structure; this is often expected but should be known."
                ),
                remediation=(
                    "Confirm LDAP exposure is limited to approved networks and document whether "
                    "anonymous RootDSE metadata is expected."
                ),
                counter_test=(
                    "Run the approved LDAP RootDSE check again from the audited network and "
                    "confirm the exposure matches the approved design."
                ),
                confidence=0.7,
            )
        )
    return findings


def _parse_ldif_attributes(output: str) -> dict[str, list[str]]:
    attributes: dict[str, list[str]] = {}
    current_key = ""
    for raw_line in output.splitlines():
        if not raw_line or raw_line.startswith("#"):
            continue
        if raw_line.startswith(" ") and current_key:
            attributes[current_key][-1] += raw_line[1:]
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        current_key = key.strip().lower()
        attributes.setdefault(current_key, []).append(value.strip())
    return attributes


def render_ldap_command(command: list[str]) -> str:
    return render_command(command)
