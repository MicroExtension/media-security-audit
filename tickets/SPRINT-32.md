# Sprint 32 - Enriched Mission Export Manifest

Goal: Make mission ZIP export packages easier to review and archive by adding
structured mission, client, template, scope, report, authorization, and evidence
metadata to `manifest.json`.

## Scope

1. Preserve the existing mission export ZIP contents.
2. Add mission name, audit type, mission status, and selected checks to the
   manifest.
3. Add client name when available.
4. Add audit template id and title when available.
5. Add authorization decision, scope summary, report counts, authorization brief
   counts, scan run counts, and evidence path counts.
6. Add tests for the enriched manifest fields.

## Safety

- No scanner execution.
- No network activity.
- No change to exported evidence or report files.
- Manifest enrichment is read-only metadata generation.

## Acceptance Criteria

- Existing manifest keys remain available.
- The manifest includes client and mission metadata.
- The manifest includes selected checks and template metadata.
- The manifest includes scope and export counters.
- Tests cover generated ZIP manifest content.
