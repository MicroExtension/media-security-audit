# Sprint 115 - Debian VM Backup Manifest Verification

## Goal

Add a guarded helper that confirms a backup sidecar manifest still matches its
archive before the backup is trusted for copy, handoff, or restore preview.

## Scope

- Add `scripts/debian-vm-verify-backup-manifest.sh`.
- Compare manifest archive name, size, SHA-256, and verification status.
- Keep verification checksum-only and restore-free.
- Document the helper in README, deployment notes, next steps, and roadmap.
- Add unit coverage that guards against scanner, service, and destructive
  behavior.

## Acceptance Criteria

- The helper accepts `<backup.tgz>` and defaults to
  `<backup.tgz>.manifest.txt`.
- A mismatch in archive name, size, SHA-256, or verification status fails.
- The helper does not extract archives or restore data.
- Deployment tests include the new helper.

## Safety

- No live scanner execution.
- No Docker service startup.
- No customer data collection.
- No destructive filesystem operations.
