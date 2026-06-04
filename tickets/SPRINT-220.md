# Sprint 220 - Pilot Final Handoff Checklist

## Goal

Add a final Pilot handoff checklist that technicians can review before evidence
archiving and client delivery closeout.

## Scope

- add a Markdown final handoff checklist export
- add a JSON final handoff checklist export
- include the checklist files in the Pilot evidence bundle
- expose the checklist from the local Pilot page
- include the checklist files in Pilot handoff, receipt, manifest, inventory,
  and verification metadata
- cover visible, exported, and archived bundle behavior with tests

## Safety

- no scanner execution is added
- no network activity is added
- no bundle extraction or restore behavior is added
- checklist items are derived from existing local Pilot readiness metadata

## Acceptance Criteria

- Pilot page links to the final handoff checklist
- Pilot ZIP contains Markdown and JSON checklist files
- manifest, inventory, and verification outputs count the new files
- handoff summary and delivery receipt include the checklist in file metadata
- checklist JSON identifies ready, attention, and manual closeout items
