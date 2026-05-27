# Sprint 177 - Pilot Bundle Inventory

## Goal

Show the pilot evidence bundle file inventory directly on the Pilot page before
download.

## Scope

- Build a file inventory from the same generated pilot evidence files used by
  the ZIP bundle and manifest.
- Show file name, byte size, and short SHA-256 on the Pilot page.
- Keep Bundle, Manifest, and Verify links grouped near the inventory.
- Keep inventory generation local, deterministic, and in memory.

## Out of Scope

- No live scanner execution.
- No network activity.
- No customer file collection.
- No disk writes for inventory generation.

## Acceptance Criteria

- The Pilot page has a Bundle inventory section.
- The inventory lists pilot evidence file names, byte sizes, and short hashes.
- Existing bundle, manifest, verification, and Markdown exports continue to work.
- Unit tests cover template wiring and inventory content.
