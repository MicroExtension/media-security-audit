# Sprint 128 - Offline Package Verification

## Goal

Give technicians a checksum-only way to verify a source-only offline update
package sidecar manifest before copying or planning maintenance on a customer
VM.

## Scope

- Add `scripts/debian-vm-verify-offline-update-package.sh`.
- Validate package name, source metadata, size, SHA-256, contents marker,
  exclusions marker, and application status.
- Reference the verification helper from the offline update plan.
- Update README, deployment notes, next steps, and roadmap.
- Extend deployment file tests.

## Acceptance Criteria

- Verification defaults to `<package.tgz>.manifest.txt`.
- Verification fails when package name, size, SHA-256, contents, exclusions, or
  application marker do not match expectations.
- The helper does not apply packages, extract archives, pull code, build images,
  restart services, collect logs, or run scanners.
- Offline update planning recommends package verification before copy.

## Safety

- No live scanner execution.
- No Git pull.
- No Docker build, run, or service startup.
- No archive extraction.
- No customer data collection.
- No destructive filesystem operations.
