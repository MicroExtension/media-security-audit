# Sprint 23 - Workspace Backup Export

## Goal

Add a controlled workspace backup export for appliance operations, migration,
and recovery.

## Scope

1. Add a workspace backup generator.
2. Include local JSON data and generated report files.
3. Add a manifest with client, mission, data file, and report file counts.
4. Add System page controls to generate and download the backup.
5. Exclude backup ZIP files from the backup contents.
6. Add unit tests for package contents, empty workspaces, and system status.

## Safety Constraints

- No scan execution is added.
- No arbitrary browser-supplied file path is accepted.
- Backup generation is read-only against audit data and generated reports.
- Existing authentication protects the System page routes.

## Acceptance Criteria

- The System page can generate a workspace backup ZIP.
- The ZIP contains `manifest.json`, data files, and generated reports.
- Existing backups are not recursively included.
- Missing backups return a named error.
- Unit tests cover the workflow without network activity.
