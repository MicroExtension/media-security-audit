# Sprint 99 - Debian VM Backup Verification Helper

## Goal

Let technicians verify that a local VM backup archive is readable and contains
the expected persistent folders before trusting it for an update.

## Scope

- Add `scripts/debian-vm-verify-backup.sh`.
- Validate archive existence and non-empty size.
- Use `tar -tzf` to list the archive without extraction.
- Check for `data`, `runs`, `reports`, and `evidence` entries.
- Add optional `--verbose` listing output.
- Update deployment documentation and static safety tests.

## Acceptance Criteria

- Verification does not extract or restore data.
- Verification fails if the archive is missing or empty.
- Verification fails if a persistent folder is absent.
- The helper does not start Docker services.
- The helper does not run scanners.

## Safety

- No scanner execution is added.
- No network target is contacted.
- The helper only reads a local archive and prints verification status.
