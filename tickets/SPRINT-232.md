# Sprint 232 - Wizard Target Guidance

## Goal

Make the guided audit wizard target step easier for technicians to complete.

## Scope

- Add compact guidance for each target field.
- Explain which target values match internal, domain, web, and AD/LDAP checks.
- Keep the change informational only.
- Do not change scanner execution.
- Do not change scope approval rules.

## Acceptance Criteria

- The target step shows guidance before target entry.
- Guidance covers internal targets, public domains, web URLs, and AD/LDAP hosts.
- The guidance is responsive on narrow screens.
- Tests verify the template and CSS hooks.

## Safety

- No scan execution added.
- No network activity added.
- No authorization bypass added.
