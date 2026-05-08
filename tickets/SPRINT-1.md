# Sprint 1 - CLI Foundation And Findings Engine

## Objective

Create the minimum useful product foundation without live scanning.

## Scope

Implement:
- Python package skeleton
- Typer CLI
- Pydantic domain models
- findings engine
- finding deduplication
- JSON export
- Markdown report rendering
- HTML report rendering
- tests

Do not implement live scanners in this sprint.

## Tasks

1. Add package structure under `app/media_security_audit/`.
2. Add CLI entrypoint `media-audit`.
3. Add models:
   - Client
   - Mission
   - ScopeItem
   - Asset
   - Finding
   - Report
4. Add severity enum.
5. Add finding fingerprint and deduplication.
6. Add JSON export.
7. Add simple Markdown report template.
8. Add simple HTML report template.
9. Add pytest unit tests.
10. Update README usage examples.

## Acceptance Criteria

- `media-audit --help` works.
- Unit tests pass.
- A sample mission can generate JSON, Markdown, and HTML reports from fixture findings.
- No command performs network activity.
- Every generated finding contains remediation and counter-test fields.

