# Sprint 218 - Pilot Handoff Category Metadata

## Goal

Make Pilot handoff artifacts consistently expose normalized evidence file categories.

## Scope

- add `category` metadata to shared Pilot bundle file details
- include categories in handoff summary JSON and Markdown tables
- include categories in bundle index JSON and Markdown tables
- include categories in delivery receipt JSON and Markdown tables
- include categories in evidence manifest entries
- include categories in evidence verification JSON and Markdown tables
- bump affected JSON schema versions
- cover exported and archived bundle behavior with tests

## Safety

- no scanner execution is added
- no network activity is added
- no bundle extraction or restore behavior is added
- the sprint only classifies existing local Pilot evidence metadata

## Acceptance Criteria

- handoff, index, receipt, manifest, and verification exports include normalized categories
- Markdown file tables show the category column
- JSON file detail entries include `category`
- archived bundle files expose the same metadata
- tests cover schema version changes and category values
