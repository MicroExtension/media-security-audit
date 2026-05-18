# Sprint 91 - Deployment Preflight CLI

## Goal

Give technicians a local command to verify appliance readiness before customer
use without running scans.

## Scope

- Add a deployment preflight helper.
- Expose `media-audit preflight`.
- Report storage, web authentication, inventory, and external tool readiness.
- Keep missing tools visible without launching them.
- Add tests and deployment notes.

## Acceptance Criteria

- Preflight reports ready, warning, or blocked status.
- Blocked storage returns a non-zero exit code.
- Warnings do not prevent execution.
- No scanner command is executed.
- The fallback argparse CLI exposes the same command.

## Safety

- This sprint only inspects local configuration and filesystem readiness.
- No scanner execution is added.
- No network activity is added.
