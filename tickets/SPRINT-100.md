# Sprint 100 - Debian VM Restore Preview Helper

## Goal

Let technicians inspect a backup restore candidate without replacing live
appliance data.

## Scope

- Add `scripts/debian-vm-restore-preview.sh`.
- Verify the backup archive before extraction.
- Extract into a unique preview folder under `reports/restore-previews`.
- Refuse to extract over live `data`, `runs`, `reports`, or `evidence` folders.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- The helper does not replace live data folders.
- The helper refuses existing preview destinations.
- The helper verifies expected persistent folders after extraction.
- The helper does not start Docker services.
- The helper does not run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted.
- Extraction is limited to an isolated preview destination for manual review.
