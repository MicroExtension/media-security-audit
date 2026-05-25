# Sprint 148 - TLS testssl.sh Foundation

## Goal

Add a guarded TLS audit foundation using `testssl.sh` without enabling any automatic scan execution.

## Scope

- Add an optional `tls` audit check.
- Build safe `testssl.sh` plan commands for approved HTTPS URL, domain, host, or IP scope.
- Require `--execute`, mission authorization, and approved scope before any live TLS run.
- Execute commands without shell invocation.
- Parse fixture JSON into normalized TLS findings.
- Store TLS findings and scan run metadata on missions.
- Add web scan plan previews for selected TLS checks.
- Update documentation and sprint tracking.

## Acceptance Criteria

- `scan tls-plan` prints planned `testssl.sh` commands only.
- `scan tls-run` refuses to run without `--execute`.
- TLS run tests use mocked runners only.
- Parsed TLS findings include severity, proof, risk, remediation, and counter-test text.
- Mission scan plan previews show TLS only when the TLS check is selected.
- Existing default mission checks remain unchanged.

## Safety

- No live `testssl.sh` execution during development.
- No browser-driven scan execution added.
- No network activity in tests.
- No destructive operation.
- All command execution remains guarded and shell-free.
