# Sprint 122 - Debian VM Bundle Inventory

## Goal

Add a read-only helper that lists handoff, maintenance, and support bundles with
sidecar manifest status.

## Scope

- Add `scripts/debian-vm-bundle-inventory.sh`.
- Support optional `--verify-manifests`.
- Cover handoff, maintenance, and support bundle directories.
- Document the helper in README, deployment notes, next steps, and roadmap.
- Extend deployment file tests for inventory guardrails.

## Acceptance Criteria

- The helper lists `media-audit-handoff-*.tgz`,
  `media-audit-maintenance-*.tgz`, and `media-audit-support-*.tgz` bundles.
- The helper reports manifest status as `missing`, `present`, `verified`, or
  `failed`.
- `--verify-manifests` exits non-zero when a manifest is missing or invalid.
- No cleanup, extraction, restore, scanner, or Docker service operation is
  introduced.

## Safety

- No live scanner execution.
- No Docker service startup.
- No customer data collection.
- No destructive filesystem operations.
