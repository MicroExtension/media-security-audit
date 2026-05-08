"""Safe Nmap dry-run adapter and XML parser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from media_security_audit.models import Finding, ScopeItem, ScopeType, Severity


NMAP_TARGET_TYPES = {
    ScopeType.CIDR,
    ScopeType.IP,
    ScopeType.HOST,
    ScopeType.DOMAIN,
}

SENSITIVE_TCP_PORTS: dict[int, tuple[str, Severity, str]] = {
    21: ("FTP", Severity.MEDIUM, "FTP often exposes credentials or legacy file transfer workflows."),
    23: ("Telnet", Severity.HIGH, "Telnet is unencrypted and should not be exposed."),
    139: ("NetBIOS/SMB", Severity.MEDIUM, "Legacy Windows file sharing exposure increases lateral movement risk."),
    389: ("LDAP", Severity.MEDIUM, "LDAP exposure may reveal directory information if not restricted."),
    445: ("SMB", Severity.MEDIUM, "SMB exposure should be restricted to trusted networks."),
    3389: ("RDP", Severity.HIGH, "RDP exposure increases remote access attack surface."),
    5985: ("WinRM", Severity.MEDIUM, "WinRM exposure should be limited to administration networks."),
    5986: ("WinRM over TLS", Severity.MEDIUM, "WinRM exposure should be limited to administration networks."),
}


@dataclass(frozen=True)
class NmapService:
    host: str
    port: int
    protocol: str
    state: str
    service: str | None = None
    product: str | None = None
    version: str | None = None


@dataclass(frozen=True)
class NmapHost:
    address: str
    hostnames: tuple[str, ...]
    services: tuple[NmapService, ...]


class NmapCommandBuilder:
    """Build conservative Nmap commands without invoking a shell."""

    def __init__(self, executable: str = "nmap") -> None:
        self.executable = executable

    def build(self, target: str, output_path: Path | None = None) -> list[str]:
        validate_nmap_target(target)
        output = str(output_path) if output_path else "-"
        return [
            self.executable,
            "-sV",
            "--version-light",
            "--top-ports",
            "100",
            "-T2",
            "--max-retries",
            "2",
            "--host-timeout",
            "5m",
            "-oX",
            output,
            target,
        ]

    def build_for_scope(self, scope: list[ScopeItem], output_dir: Path | None = None) -> list[list[str]]:
        targets = approved_nmap_targets(scope)
        commands = []
        for index, target in enumerate(targets, start=1):
            output_path = output_dir / f"nmap-{index}.xml" if output_dir else None
            commands.append(self.build(target, output_path=output_path))
        return commands


def approved_nmap_targets(scope: list[ScopeItem]) -> list[str]:
    targets = []
    for item in scope:
        if item.approved and not item.excluded and item.type in NMAP_TARGET_TYPES:
            validate_nmap_target(item.value)
            targets.append(item.value)
    return targets


def validate_nmap_target(target: str) -> None:
    if target.startswith("-"):
        raise ValueError("Nmap target cannot start with '-'")
    if any(character.isspace() for character in target):
        raise ValueError("Nmap target cannot contain whitespace")


def render_command(command: list[str]) -> str:
    """Render a command for display only. Do not pass this string to a shell."""

    return " ".join(_quote_arg(part) for part in command)


def parse_nmap_xml(xml_content: str) -> list[NmapHost]:
    root = ET.fromstring(xml_content)
    hosts: list[NmapHost] = []

    for host_element in root.findall("host"):
        status = host_element.find("status")
        if status is not None and status.attrib.get("state") != "up":
            continue

        address_element = host_element.find("address")
        if address_element is None:
            continue

        address = address_element.attrib.get("addr", "")
        hostnames = tuple(
            hostname.attrib.get("name", "")
            for hostname in host_element.findall("./hostnames/hostname")
            if hostname.attrib.get("name")
        )
        services = []

        for port_element in host_element.findall("./ports/port"):
            state_element = port_element.find("state")
            state = state_element.attrib.get("state", "") if state_element is not None else ""
            if state != "open":
                continue

            service_element = port_element.find("service")
            services.append(
                NmapService(
                    host=address,
                    port=int(port_element.attrib["portid"]),
                    protocol=port_element.attrib.get("protocol", "tcp"),
                    state=state,
                    service=_optional_attr(service_element, "name"),
                    product=_optional_attr(service_element, "product"),
                    version=_optional_attr(service_element, "version"),
                )
            )

        hosts.append(NmapHost(address=address, hostnames=hostnames, services=tuple(services)))

    return hosts


def parse_nmap_xml_file(path: Path) -> list[NmapHost]:
    return parse_nmap_xml(path.read_text(encoding="utf-8"))


def findings_from_services(services: list[NmapService]) -> list[Finding]:
    findings = []
    for service in services:
        sensitive = SENSITIVE_TCP_PORTS.get(service.port)
        if sensitive:
            label, severity, risk = sensitive
            findings.append(
                Finding(
                    title=f"Sensitive service reachable: {label}",
                    severity=severity,
                    affected_asset=f"{service.host}:{service.port}/{service.protocol}",
                    category="network_exposure",
                    source_module="nmap",
                    proof=_service_proof(service),
                    risk=risk,
                    remediation=(
                        "Restrict access to trusted administration networks or VPN users, "
                        "and confirm the service is required."
                    ),
                    counter_test=(
                        "Run the approved Nmap check again and confirm the port is no longer "
                        "reachable from the audited network."
                    ),
                    confidence=0.85,
                )
            )
        else:
            findings.append(
                Finding(
                    title="Open network service detected",
                    severity=Severity.INFO,
                    affected_asset=f"{service.host}:{service.port}/{service.protocol}",
                    category="network_inventory",
                    source_module="nmap",
                    proof=_service_proof(service),
                    risk="Open services increase the asset inventory that must be maintained and monitored.",
                    remediation="Confirm that the service is expected, patched, and restricted where possible.",
                    counter_test="Run the approved Nmap check again and confirm the expected exposure.",
                    confidence=0.75,
                )
            )
    return findings


def findings_from_hosts(hosts: list[NmapHost]) -> list[Finding]:
    services = [service for host in hosts for service in host.services]
    return findings_from_services(services)


def _service_proof(service: NmapService) -> str:
    details = [f"{service.protocol}/{service.port} open"]
    if service.service:
        details.append(f"service={service.service}")
    if service.product:
        details.append(f"product={service.product}")
    if service.version:
        details.append(f"version={service.version}")
    return "; ".join(details)


def _optional_attr(element: ET.Element | None, attribute: str) -> str | None:
    if element is None:
        return None
    value = element.attrib.get(attribute)
    return value or None


def _quote_arg(value: str) -> str:
    if not value or any(char.isspace() for char in value):
        return '"' + value.replace('"', '\\"') + '"'
    return value
