# Sprint 33 - Mission Export Checksums

Goal: Add per-file integrity metadata to mission export manifests so handoff ZIP
packages can be verified after transfer or archival.

## Scope

1. Preserve the existing mission export ZIP contents.
2. Prepare each packaged file as a traced archive member before writing the ZIP.
3. Add `manifest_version`, `archive_file_count`, and `archive_files` to the
   manifest.
4. Include path, size, and SHA-256 for each packaged file except the manifest
   itself.
5. Add tests that compare manifest hashes with actual ZIP member bytes.

## Safety

- No scanner execution.
- No network activity.
- No change to mission data or findings.
- Checksums are generated locally from files already being packaged.

## Acceptance Criteria

- Existing manifest fields remain available.
- Every packaged data, report, authorization, activity, and run file has a
  checksum entry.
- Manifest entries include file path, byte size, and SHA-256 hash.
- Tests verify at least one checksum against the ZIP content.
