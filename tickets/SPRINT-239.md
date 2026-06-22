# Sprint 239 - Consolidated UX Test Pass

## Goal

Bundle the product-owner UX feedback into one testable sprint so the first VM
trial can focus on navigation, audit creation flow, CVE catalog visibility, and
clear scan progress expectations.

## Scope

1. Add dedicated Clients and Audits pages.
2. Keep the top navigation aligned with those pages.
3. Extend the guided audit wizard with a guarded credential review step.
4. Block credential review creation unless guardrails are explicitly confirmed.
5. Keep CVE/KEV catalog and scan-progress work visible from the product flow.
6. Update tests and documentation for the consolidated workflow.

## Acceptance Criteria

- `/clients` shows client creation, client metrics, and next actions.
- `/audits` shows audit status groups, quick mission creation, and the full mission list.
- The guided audit wizard includes a Credentials step before Review.
- Credential review metadata can be recorded only with explicit guardrail confirmation.
- The wizard still blocks final creation when client, mission, scope, service coverage, or
  credential guardrails are incomplete.
- Tests cover the new pages, wizard markers, backend guardrail validation, and styles.

## Safety

- No brute force automation is added.
- No exploit automation is added.
- Credential review is recorded as approved planning metadata only.
- Live credential validation remains a separate future module with written authorization,
  rate limits, logging, and explicit scope.
