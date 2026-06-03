# Sprint 215 - Pilot Archive Bytes Manifest Alignment

## Goal

Keep the Pilot archive byte summary aligned with the manifest generator.

## Scope

- share the manifest payload builder between real manifests and visible archive byte summaries
- keep `Archive Bytes` based on the same JSON payload shape as `manifest.json`
- add a test comparing `Archive Bytes` to evidence bytes plus public manifest size
- keep bundle contents, manifests, CSV, and JSON export behavior unchanged

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore behavior
- no customer data collection

## Acceptance Criteria

- archive byte summaries use the shared manifest payload builder
- default Pilot view archive bytes equal visible evidence bytes plus public manifest bytes
- existing bundle exports remain covered by tests
- no scanner or network behavior changes
