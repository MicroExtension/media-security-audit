# Sprint 147 - Counter-Test Next Actions

## Goal

Route mission next actions to failed counter-tests when remediation follow-up is needed.

## Scope

- Prioritize failed counter-test warnings over new finding review warnings.
- Link dashboard, client, and mission next actions to `#counter-test`.
- Keep blocked setup, scope, and check issues higher priority.
- Update documentation and tests.

## Acceptance Criteria

- A mission with failed counter-tests has warning preparation status.
- Its next action says `Review N failed counter-test(s).`
- Its next action label is `Open Counter-tests`.
- The action URL targets `#counter-test`.
- New finding warnings remain supported.
- Blocked mission issues still take priority.
- No scanner execution, network activity, or deployment workflow is added.

## Safety

- No live scanner execution.
- No browser scan execution.
- No network activity added.
- No destructive test.
- This sprint only changes stored-status navigation.
