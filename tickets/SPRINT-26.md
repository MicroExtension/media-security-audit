# Sprint 26 - Finding Remediation Suggestions

## Goal

Show relevant remediation library suggestions directly on mission findings so
technicians can compare a finding with standard remediation guidance during
review.

## Scope

1. Link finding categories to built-in remediation library entries.
2. Add read-only related remediation suggestions to finding view models.
3. Render suggestions under matching mission finding cards.
4. Keep manual finding content unchanged.
5. Add tests for matching and no-match cases.

## Safety Constraints

- Suggestions are read-only.
- No finding field is overwritten automatically.
- No scan execution is added.
- Matching is local and category-based only.

## Acceptance Criteria

- Findings with known categories show matching library suggestions.
- Findings without matching categories remain unchanged.
- Suggestions include remediation and counter-test text.
- Unit tests cover the view-model integration.
