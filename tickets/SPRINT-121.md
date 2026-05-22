# Sprint 121 - Debian VM Bundle Manifest Verification

## Goal

Add a checksum-only verification helper for sidecar manifests created by
handoff, maintenance, and support bundles.

## Scope

- Add `scripts/debian-vm-verify-bundle-manifest.sh`.
- Validate bundle name, size, SHA-256, source report, and expected contents.
- Keep verification generic for handoff, maintenance, and support bundles.
- Document the helper in README, deployment notes, next steps, and roadmap.
- Extend deployment file tests for manifest verification guardrails.

## Acceptance Criteria

- The helper accepts `<bundle.tgz>` and defaults to
  `<bundle.tgz>.manifest.txt`.
- A mismatch in bundle name, size, SHA-256, source report, or contents fails.
- The helper does not extract archives or restore data.
- Deployment tests include the new helper.

## Safety

- No live scanner execution.
- No Docker service startup.
- No customer data collection.
- No destructive filesystem operations.
