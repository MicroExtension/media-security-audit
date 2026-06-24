# Final VM Appliance Target

This document defines the target delivery model for the MEDIA Security Audit
appliance.

## Delivery Formats

The final customer delivery should provide:

- VMware: exported OVA from a prepared Ubuntu/Debian VM.
- Hyper-V: exported VHDX or exported Hyper-V VM folder.
- Source fallback: private GitHub repository plus VM bootstrap procedure.
- Offline update fallback: source-only update package and sidecar manifest.

## Baseline VM

Recommended appliance baseline:

- Ubuntu Server LTS or Debian stable.
- 2 vCPU minimum, 4 vCPU recommended for larger internal ranges.
- 4 GB RAM minimum, 8 GB recommended.
- 40 GB disk minimum.
- One network adapter on the authorized audit network.
- DHCP reservation or static IP.
- Outbound HTTPS allowed for first install, updates, and optional CVE catalog
  refresh.

## Preconfiguration Checklist

Build the golden VM before customer delivery:

```bash
sudo apt update
sudo apt install -y git docker.io curl ca-certificates nmap smbclient ldap-utils
```

Install Docker Compose v2 with the package available on the distribution:

```bash
sudo apt install -y docker-compose-plugin || sudo apt install -y docker-compose-v2
```

Optional TLS live checks:

```bash
sudo apt install -y testssl.sh
```

Then prepare the application:

```bash
git clone https://github.com/MicroExtension/media-security-audit.git
cd media-security-audit
bash scripts/debian-vm-bootstrap.sh
bash scripts/debian-vm-bootstrap.sh --confirm --init-env
```

Log out and back in if the bootstrap helper adds the technician user to the
Docker group.

Start and validate:

```bash
cd ~/media-security-audit
bash scripts/debian-vm-preflight.sh
bash scripts/debian-vm-start.sh
bash scripts/debian-vm-status.sh
bash scripts/debian-vm-ui-smoke-test.sh
```

The generated web password must be stored in the maintenance password vault
before the VM is exported or delivered.

## Customer Finalization

At customer site:

1. Assign the final VM network.
2. Confirm the UI remains bound to `127.0.0.1` unless VPN/firewall access is
   approved.
3. Confirm the customer audit scope is written and stored outside the tool.
4. Run `bash scripts/debian-vm-security-review.sh`.
5. Run `bash scripts/debian-vm-ui-smoke-test.sh`.
6. Open `http://127.0.0.1:8080/test-readiness`.
7. Create the customer client record and analysis session from the guided audit
   wizard.

## Export Notes

Before exporting an OVA or VHDX:

- remove customer test data if the VM is a reusable template
- keep `.env` protected with mode `600`
- keep authentication enabled
- do not include application logs in customer handoff bundles
- snapshot only after the smoke test report is reviewed

The VM image is a deployment artifact. The private GitHub repository remains
the source of truth.
