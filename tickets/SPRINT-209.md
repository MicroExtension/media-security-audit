# Sprint 209 - Pilot Inventory Review Column

## Goal

Show the Pilot evidence bundle review order directly in the visible Pilot page inventory.

## Scope

- add review order metadata to visible Pilot evidence file rows
- show a `Review` column in the Pilot bundle table
- keep bundle contents, manifests, CSV, and JSON export behavior unchanged
- cover review order values in tests

## Safety

- no live scanner changes
- no network activity
- no bundle extraction or restore behavior
- no customer data collection

## Acceptance Criteria

- Pilot page template renders a `Review` column
- visible evidence rows expose `item.review_order`
- review numbers run from 1 through 15 in handoff review order
- existing bundle exports remain covered by tests
