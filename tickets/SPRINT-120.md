# Sprint 120 - Debian VM Bundle Manifests

## Goal

Add sidecar manifests to shareable VM bundles so technicians can verify basic
integrity after copying them outside the customer site.

## Scope

- Update handoff, maintenance, and support bundle helpers.
- Write `<bundle.tgz>.manifest.txt` with generated time, bundle name, size,
  SHA-256, source report, and expected single-report contents.
- Keep bundles limited to one report file.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests for bundle manifest guardrails.

## Acceptance Criteria

- Handoff, maintenance, and support bundles each write a sidecar manifest.
- Each manifest includes `size_bytes`, `sha256`, `source_report`, and
  single-report `contents`.
- Bundle helpers still do not package repository root, persistent folders,
  customer data, or application logs.
- No scanner, Docker service startup, extraction, restore, or destructive
  operation is introduced.

## Safety

- No live scanner execution.
- No Docker service startup.
- No customer data collection.
- No destructive filesystem operations.
