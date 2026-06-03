# Sprint 210 - Pilot Inventory Purpose Column

## Goal

Show why each Pilot evidence bundle file exists directly in the visible Pilot page inventory.

## Scope

- add purpose metadata to visible Pilot evidence file rows
- show a `Purpose` column in the Pilot bundle table
- reuse the existing Pilot bundle file purpose mapping
- keep bundle contents, manifests, CSV, and JSON export behavior unchanged
- cover visible purpose values in tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore behavior
- no customer data collection

## Acceptance Criteria

- Pilot page template renders a `Purpose` column
- visible evidence rows expose `item.purpose`
- purpose values match the existing Pilot bundle purpose mapping
- existing bundle exports remain covered by tests
