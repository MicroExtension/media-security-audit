# Sprint 5 - Appliance Deployment Foundation

## Objective

Prepare the application for repeatable local appliance deployment.

## Scope

Implement:
- Dockerfile
- docker-compose.yml
- persistent volumes
- environment configuration
- first setup command
- health check endpoint
- external tool availability check
- backup/export script

## Acceptance Criteria

- app can run through Docker Compose
- reports and evidence persist across restarts
- health endpoint reports application status
- tool check reports available scanners
- backup script creates a timestamped archive of config, data, reports, and evidence

