"""Shared audit check target requirements."""

from __future__ import annotations

from media_security_audit.models import AuditCheck, ScopeType


CHECK_SCOPE_TYPES: dict[AuditCheck, tuple[ScopeType, ...]] = {
    AuditCheck.NMAP: (
        ScopeType.CIDR,
        ScopeType.IP,
        ScopeType.HOST,
        ScopeType.DOMAIN,
    ),
    AuditCheck.HTTP_HEADERS: (ScopeType.URL,),
    AuditCheck.DNS_MAIL: (ScopeType.DOMAIN,),
    AuditCheck.TLS: (
        ScopeType.URL,
        ScopeType.DOMAIN,
        ScopeType.HOST,
        ScopeType.IP,
    ),
    AuditCheck.SMB: (
        ScopeType.HOST,
        ScopeType.IP,
        ScopeType.DOMAIN,
    ),
    AuditCheck.LDAP: (
        ScopeType.HOST,
        ScopeType.IP,
        ScopeType.DOMAIN,
    ),
}


CHECK_SCOPE_REQUIREMENTS: dict[AuditCheck, str] = {
    AuditCheck.NMAP: "approved CIDR, IP, host, or domain scope",
    AuditCheck.HTTP_HEADERS: "approved URL scope",
    AuditCheck.DNS_MAIL: "approved domain scope",
    AuditCheck.TLS: "approved URL, domain, host, or IP scope",
    AuditCheck.SMB: "approved host, IP, or domain scope",
    AuditCheck.LDAP: "approved host, IP, or domain scope",
}
