# Sprint 217 - Pilot Inventory File Categories

## Goal

Expose normalized Pilot evidence file categories in the visible bundle inventory and inventory exports.

## Scope

- add a stable `category` value for Pilot evidence files
- show the category on the Pilot bundle inventory table
- include categories in Pilot inventory CSV exports
- include categories in Pilot inventory JSON exports
- bump the inventory JSON schema version to 4
- cover visible, CSV, JSON, and archived bundle inventory behavior with tests

## Safety

- no scanner execution is added
- no network activity is added
- no bundle extraction or restore behavior is added
- the change only classifies existing local evidence export metadata

## Acceptance Criteria

- Pilot bundle inventory rows show a category column
- inventory CSV rows include `category`
- inventory JSON file entries include `category`
- archived bundle inventory JSON uses schema version 4
- tests verify human and automation category values
