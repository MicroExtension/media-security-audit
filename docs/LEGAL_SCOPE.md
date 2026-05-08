# Legal Scope And Rules Of Engagement

This document defines the minimum engagement rules for every audit mission.

## Required Before Any Scan

- written authorization from the customer
- named customer representative
- emergency contact
- authorized domains, IPs, CIDRs, URLs, and systems
- forbidden systems and blackout periods
- audit window
- data handling requirements
- report recipients

## Default Safe Rules

- no denial-of-service testing
- no brute force
- no password spraying
- no exploitation automation
- no payload deployment
- no post-exploitation
- no exfiltration
- no destructive tests
- no persistence
- no lateral movement

## Evidence Rules

Evidence must be:
- minimal
- relevant
- non-sensitive whenever possible
- stored in the mission evidence directory
- referenced in findings without exposing secrets

## Stop Conditions

Stop the mission and notify the client contact if:
- a scan causes service instability
- credentials or sensitive data are discovered
- scope is ambiguous
- a critical exposure is found that requires urgent containment
- customer revokes authorization

## Counter-Test

Every remediation must have a safe counter-test procedure.

Counter-tests should prove that the issue is fixed without exploiting the
original weakness.

