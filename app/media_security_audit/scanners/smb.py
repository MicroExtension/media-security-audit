"""Guarded smbclient adapter and anonymous listing parser."""

from __future__ import annotations

import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from media_security_audit.models import Finding, ScopeItem, ScopeType, Severity
from media_security_audit.scanners.nmap import render_command


SMB_TARGET_TYPES = {
    ScopeType.IP,
    ScopeType.HOST,
    ScopeType.DOMAIN,
}

HIDDEN_ADMIN_SHARE_SUFFIX = "$"


@dataclass(frozen=True)
class SmbShare:
    target: str
    share_type: str
    name: str
    comment: str = ""


@dataclass(frozen=True)
class SmbExecutionResult:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    target: str


SmbRunner = Callable[[list[str], int], subprocess.CompletedProcess[str]]
ExecutableLookup = Callable[[str], str | None]


class SmbCommandBuilder:
    """Build conservative smbclient anonymous listing commands."""

    def __init__(self, executable: str = "smbclient") -> None:
        self.executable = executable

    def build(self, target: str) -> list[str]:
        normalized_target = validate_smb_target(target)
        return [
            self.executable,
            "-L",
            f"//{normalized_target}",
            "-N",
            "-g",
            "--option=client min protocol=SMB2",
            "--option=client max protocol=SMB3",
        ]

    def build_for_scope(self, scope: list[ScopeItem]) -> list[list[str]]:
        return [self.build(target) for target in approved_smb_targets(scope)]


class SmbExecutor:
    """Execute pre-built smbclient commands with guardrails."""

    def __init__(
        self,
        runner: SmbRunner | None = None,
        executable_lookup: ExecutableLookup = shutil.which,
        timeout_seconds: int = 120,
    ) -> None:
        self.runner = runner or self._default_runner
        self.executable_lookup = executable_lookup
        self.timeout_seconds = timeout_seconds

    def run(self, command: list[str]) -> SmbExecutionResult:
        validate_smb_command(command)
        executable = command[0]
        if self.executable_lookup(executable) is None:
            raise FileNotFoundError(f"smbclient executable not found: {executable}")

        completed = self.runner(command, self.timeout_seconds)
        return SmbExecutionResult(
            command=tuple(command),
            exit_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            target=smb_target_from_command(command),
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


def approved_smb_targets(scope: list[ScopeItem]) -> list[str]:
    targets = []
    seen = set()
    for item in scope:
        if item.approved and not item.excluded and item.type in SMB_TARGET_TYPES:
            target = validate_smb_target(item.value)
            if target not in seen:
                targets.append(target)
                seen.add(target)
    return targets


def validate_smb_target(target: str) -> str:
    value = target.strip()
    if not value:
        raise ValueError("SMB audit target is required")
    if value.startswith("-"):
        raise ValueError("SMB audit target cannot start with '-'")
    if any(character.isspace() for character in value):
        raise ValueError("SMB audit target cannot contain whitespace")
    if "://" in value or "/" in value or "\\" in value or "@" in value:
        raise ValueError("SMB audit target must be a bare host, IP, or domain")
    return value.lower()


def validate_smb_command(command: list[str]) -> None:
    if not command:
        raise ValueError("smbclient command cannot be empty")
    if command[0].startswith("-"):
        raise ValueError("smbclient executable cannot start with '-'")
    credential_flags = {"-U", "--user", "-A", "--authentication-file"}
    if any(flag in command for flag in credential_flags):
        raise ValueError("credentialed SMB checks are not allowed by the basic adapter")
    if "-c" in command or "--command" in command:
        raise ValueError("interactive smbclient commands are not allowed")
    if "-m" in command or any("protocol=nt1" in item.lower() for item in command):
        raise ValueError("SMBv1 forcing is not allowed by the basic adapter")
    smb_target_from_command(command)


def smb_target_from_command(command: list[str]) -> str:
    try:
        index = command.index("-L")
    except ValueError as error:
        raise ValueError("smbclient command must include -L") from error
    if index + 1 >= len(command):
        raise ValueError("smbclient command is missing the -L target")
    listing_target = command[index + 1]
    if not listing_target.startswith("//"):
        raise ValueError("smbclient -L target must use //host form")
    return validate_smb_target(listing_target.removeprefix("//"))


def parse_smbclient_listing(output: str, target: str) -> list[SmbShare]:
    normalized_target = validate_smb_target(target)
    shares = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 2:
            continue
        share_type = parts[0].strip()
        name = parts[1].strip()
        comment = parts[2].strip() if len(parts) > 2 else ""
        if share_type.lower() not in {"disk", "ipc", "printer"} or not name:
            continue
        shares.append(
            SmbShare(
                target=normalized_target,
                share_type=share_type,
                name=name,
                comment=comment,
            )
        )
    return shares


def findings_from_smb_shares(shares: list[SmbShare]) -> list[Finding]:
    findings = []
    by_target: dict[str, list[SmbShare]] = defaultdict(list)
    for share in shares:
        by_target[share.target].append(share)

    for target, target_shares in sorted(by_target.items()):
        disk_shares = [
            share.name
            for share in target_shares
            if share.share_type.lower() == "disk"
            and not share.name.endswith(HIDDEN_ADMIN_SHARE_SUFFIX)
        ]
        if disk_shares:
            findings.append(
                Finding(
                    title="Anonymous SMB listing exposes disk shares",
                    severity=Severity.MEDIUM,
                    affected_asset=target,
                    category="smb",
                    source_module="smbclient",
                    proof=f"Anonymous SMB listing returned disk shares: {', '.join(disk_shares)}.",
                    risk=(
                        "Anonymous SMB enumeration can reveal file share names and help an "
                        "attacker prioritize access attempts."
                    ),
                    remediation=(
                        "Disable anonymous SMB enumeration and restrict share visibility to "
                        "authenticated, authorized users."
                    ),
                    counter_test=(
                        "Run the approved SMB anonymous listing check again and confirm no "
                        "non-administrative disk shares are listed."
                    ),
                    confidence=0.85,
                )
            )
            continue

        if target_shares:
            share_summary = ", ".join(
                f"{share.share_type}:{share.name}" for share in target_shares
            )
            findings.append(
                Finding(
                    title="Anonymous SMB listing is available",
                    severity=Severity.LOW,
                    affected_asset=target,
                    category="smb",
                    source_module="smbclient",
                    proof=f"Anonymous SMB listing returned entries: {share_summary}.",
                    risk=(
                        "Anonymous SMB responses disclose service metadata to "
                        "unauthenticated clients."
                    ),
                    remediation=(
                        "Restrict anonymous SMB enumeration where business compatibility allows."
                    ),
                    counter_test=(
                        "Run the approved SMB anonymous listing check again and confirm the "
                        "server refuses unauthenticated listing."
                    ),
                    confidence=0.75,
                )
            )

    return findings


def render_smb_command(command: list[str]) -> str:
    return render_command(command)
