# Sprint 149 - SMB Basic Audit Foundation

## Goal

Add a guarded SMB basic audit foundation for anonymous listing checks without
running live SMB traffic during development.

## Scope

- Add optional `smb` audit check and labels.
- Build safe `smbclient` plan commands for approved host, IP, or domain scope.
- Require `--execute`, mission authorization, and approved scope before any live SMB run.
- Execute commands without shell invocation.
- Reject credentialed, interactive, and SMBv1-forcing command shapes.
- Parse fixture `smbclient -g` output into normalized SMB findings.
- Store SMB findings, evidence, and scan run metadata on missions.
- Add web scan plan previews for selected SMB checks.
- Install `smbclient` in the Docker image for future appliance readiness.

## Acceptance Criteria

- `scan smb-plan` prints planned `smbclient` commands only.
- `scan smb-run` refuses to run without `--execute`.
- SMB run tests use mocked runners only.
- Parsed SMB findings include severity, proof, risk, remediation, and counter-test text.
- Mission scan plan previews show SMB only when the SMB check is selected.
- Existing default mission checks remain unchanged.

## Safety

- No live SMB execution during development.
- No credentialed SMB checks.
- No interactive share commands.
- No SMBv1-forcing command shape.
- No browser-driven scan execution added.
- All command execution remains guarded and shell-free.
