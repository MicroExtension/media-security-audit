# Sprint 97 - Debian VM Backup Helper

## Goal

Give technicians a safe local backup command before updates or customer-impacting
maintenance on the appliance VM.

## Scope

- Add a guarded `scripts/debian-vm-backup.sh` helper.
- Archive persistent `data`, `runs`, `reports`, and `evidence` folders.
- Exclude `reports/backups` to avoid recursive backup archives.
- Allow `MEDIA_AUDIT_BACKUP_DIR` to override the backup destination.
- Force shell scripts to LF line endings through `.gitattributes`.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper refuses to run when persistent folders are missing.
- The helper writes timestamped `.tgz` archives.
- The helper does not start Docker services.
- The helper does not install packages or call `sudo`.
- The helper does not run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted.
- The helper only reads local persistent folders and writes a local archive.
