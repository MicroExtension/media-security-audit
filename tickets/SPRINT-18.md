# Sprint 18 - Web System Status

## Goal

Show appliance readiness from the local web UI so technicians can validate a
deployment before using it for a customer audit.

## Scope

1. Add a system status view model for authentication, storage, and tools.
2. Add a protected `/system` web page.
3. Add top navigation to the system page.
4. Show data and report directory readiness.
5. Show external tool availability without executing those tools.
6. Add tests for safe status generation.

## Safety Constraints

- No scan execution route in the web application.
- No live network requests.
- External tool checks must use path resolution only.
- The page must not run Nmap, testssl.sh, Nuclei, SMB, or LDAP commands.

## Acceptance Criteria

- The System page is reachable from top navigation.
- Authentication status is visible.
- Data and report directory status is visible.
- External tool availability is visible.
- Unit tests confirm status generation does not execute tools.
