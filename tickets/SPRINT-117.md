# Sprint 117 - Debian VM Backup Inventory

## Goal

Add a read-only helper that lets a technician list local backup archives and
sidecar manifest status before maintenance or handoff.

## Scope

- Add `scripts/debian-vm-backup-inventory.sh`.
- Support an optional `--verify-manifests` mode.
- Keep the helper read-only and restore-free.
- Document the helper in README, deployment notes, next steps, and roadmap.
- Extend deployment file tests for the new guardrails.

## Acceptance Criteria

- The helper lists `media-audit-backup-*.tgz` archives from
  `MEDIA_AUDIT_BACKUP_DIR` or `reports/backups`.
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
