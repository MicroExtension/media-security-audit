# Sprint 2 - Safe Nmap Adapter

## Objective

Add the first real scanner adapter with safe defaults and deterministic parser
tests.

## Scope

Implement:
- Nmap command builder
- safe default flags
- scope validation before execution
- dry-run mode
- XML output parser
- normalized assets
- findings for risky exposed services
- fixture-based tests

First implementation must plan commands only. It must not execute Nmap.

## Safe Defaults

Use conservative scanning defaults:
- no brute force NSE scripts
- no exploit NSE scripts
- no aggressive timing by default
- no version intensity tuning above safe defaults
- no UDP scan in the initial implementation unless explicitly approved

## Acceptance Criteria

- command builder never uses shell string concatenation
- dry-run prints the planned command
- parser tests use static XML fixtures
- scan execution requires a mission id and validated scope
- findings include remediation and counter-test guidance
