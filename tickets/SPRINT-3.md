# Sprint 3 - HTTP, DNS, Mail, And TLS Checks

## Objective

Add the first external perimeter checks.

## Scope

Implement:
- HTTP headers audit
- DNS record audit
- SPF detection
- DKIM selector configuration support
- DMARC policy audit
- testssl.sh adapter interface
- normalized findings
- report sections by category

## Acceptance Criteria

- checks are non-destructive
- DNS checks have unit tests with mocked responses
- HTTP checks have unit tests with mocked responses
- HTTP execution requires approved URL scope and explicit `--execute`
- DNS/Mail execution requires approved domain scope and explicit `--execute`
- DKIM checks require explicit selector configuration
- TLS adapter supports dry-run and fixture parsing
- findings are deduplicated across reruns
