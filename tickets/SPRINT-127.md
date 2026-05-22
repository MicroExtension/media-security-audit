# Sprint 127 - Offline Update Package

## Goal

Create a maintainer-side helper that produces a source-only offline update
package with a sidecar manifest for customer VMs without internet access.

## Scope

- Add `scripts/debian-vm-offline-update-package.sh`.
- Generate packages from tracked Git files only.
- Require a clean `main` branch before packaging.
- Write a sidecar manifest with source commit, size, and SHA-256 metadata.
- Update README, deployment notes, next steps, roadmap, and owner intervention
  notes.
- Extend deployment file tests.

## Acceptance Criteria

- Offline update packages are generated with `git archive`.
- Packages exclude `.git`, `.env`, `data`, `runs`, `reports`, and `evidence`.
- The helper does not apply packages, extract archives, pull code, build images,
  restart services, collect logs, or run scanners.
- The generated manifest can be consumed by the offline update plan helper.

## Safety

- No live scanner execution.
- No Git pull.
- No Docker build, run, or service startup.
- No archive extraction.
- No customer data collection.
- No destructive filesystem operations.
