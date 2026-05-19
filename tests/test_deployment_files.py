from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeploymentFileTests(unittest.TestCase):
    def test_shell_scripts_are_forced_to_lf_line_endings(self) -> None:
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")

        self.assertIn("*.sh text eol=lf", attributes)

    def test_dockerfile_uses_non_root_user_and_local_web_command(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("apt-get install -y --no-install-recommends", dockerfile)
        self.assertIn("nmap", dockerfile)
        self.assertIn("USER mediaaudit", dockerfile)
        self.assertIn("/var/lib/media-audit/data", dockerfile)
        self.assertIn("/var/lib/media-audit/reports", dockerfile)
        self.assertIn('"--reports-dir", "/var/lib/media-audit/reports"', dockerfile)
        self.assertIn('"--host", "0.0.0.0"', dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)

    def test_compose_defaults_to_localhost_and_persistent_volumes(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("${MEDIA_AUDIT_BIND:-127.0.0.1}:${MEDIA_AUDIT_PORT:-8080}:8080", compose)
        self.assertIn("./data:/var/lib/media-audit/data", compose)
        self.assertIn("./runs:/var/lib/media-audit/runs", compose)
        self.assertIn("./reports:/var/lib/media-audit/reports", compose)
        self.assertIn("./evidence:/var/lib/media-audit/evidence", compose)
        self.assertIn("--reports-dir", compose)
        self.assertIn("/var/lib/media-audit/reports", compose)
        self.assertIn("restart: unless-stopped", compose)
        self.assertIn('user: "${MEDIA_AUDIT_UID:-10001}:${MEDIA_AUDIT_GID:-10001}"', compose)

    def test_env_example_keeps_lan_exposure_explicit(self) -> None:
        env_example = (ROOT / ".env.example").read_text(encoding="utf-8")

        self.assertIn("MEDIA_AUDIT_BIND=127.0.0.1", env_example)
        self.assertIn("MEDIA_AUDIT_PORT=8080", env_example)
        self.assertIn("MEDIA_AUDIT_UID=10001", env_example)
        self.assertIn("MEDIA_AUDIT_GID=10001", env_example)
        self.assertIn("MEDIA_AUDIT_REQUIRE_AUTH=true", env_example)
        self.assertIn("MEDIA_AUDIT_WEB_USERNAME=admin", env_example)
        self.assertIn("MEDIA_AUDIT_WEB_PASSWORD=", env_example)
        self.assertIn("MEDIA_AUDIT_BIND=0.0.0.0", env_example)

    def test_compose_requires_web_password_before_starting(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("MEDIA_AUDIT_REQUIRE_AUTH", compose)
        self.assertIn("MEDIA_AUDIT_WEB_USERNAME", compose)
        self.assertIn("MEDIA_AUDIT_WEB_PASSWORD", compose)
        self.assertIn("Set MEDIA_AUDIT_WEB_PASSWORD in .env before starting", compose)

    def test_debian_vm_init_env_script_generates_local_only_auth_config(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-init-env.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("python3", script)
        self.assertIn("secrets.token_urlsafe(24)", script)
        self.assertIn('[[ ! -e ".env" ]]', script)
        self.assertIn("MEDIA_AUDIT_BIND=127.0.0.1", script)
        self.assertIn("MEDIA_AUDIT_REQUIRE_AUTH=true", script)
        self.assertIn("MEDIA_AUDIT_WEB_USERNAME=admin", script)
        self.assertIn("MEDIA_AUDIT_WEB_PASSWORD=${PASSWORD}", script)
        self.assertIn("chmod 600", script)
        self.assertIn("maintenance password vault", script)
        self.assertNotIn("MEDIA_AUDIT_BIND=0.0.0.0", script.splitlines())
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_rotate_password_script_is_explicit_and_auth_preserving(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-rotate-password.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("--confirm", script)
        self.assertIn("explicit --confirm is required", script)
        self.assertIn('[[ -f ".env" ]]', script)
        self.assertIn('[[ -w ".env" ]]', script)
        self.assertIn("secrets.token_urlsafe(24)", script)
        self.assertIn('BACKUP=".env.${TIMESTAMP}.bak"', script)
        self.assertIn('cp -p ".env" "${BACKUP}"', script)
        self.assertIn("MEDIA_AUDIT_REQUIRE_AUTH", script)
        self.assertIn("MEDIA_AUDIT_WEB_PASSWORD", script)
        self.assertIn('upsert("MEDIA_AUDIT_REQUIRE_AUTH", "true")', script)
        self.assertIn("chmod 600", script)
        self.assertIn("maintenance password vault", script)
        self.assertIn("scripts/debian-vm-restart.sh --confirm", script)
        self.assertNotIn('echo "${PASSWORD}"', script)
        self.assertNotIn("docker compose up", script)
        self.assertNotIn("docker compose restart", script)
        self.assertNotIn("docker compose down", script)
        self.assertNotIn("docker compose logs", script)
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_preflight_script_is_safe_and_scanner_free(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-preflight.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("MEDIA_AUDIT_WEB_PASSWORD", script)
        self.assertIn("docker compose config --quiet", script)
        self.assertIn("docker compose build media-audit", script)
        self.assertIn("docker compose run --rm media-audit preflight", script)
        self.assertIn("--strict", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_start_script_requires_preflight_before_up(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-start.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("MEDIA_AUDIT_WEB_PASSWORD", script)
        self.assertIn("bash scripts/debian-vm-preflight.sh", script)
        self.assertIn("docker compose up -d", script)
        self.assertIn("docker compose ps", script)
        self.assertLess(
            script.index("bash scripts/debian-vm-preflight.sh"),
            script.index("docker compose up -d"),
        )
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_status_script_is_read_only_and_log_free(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-status.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("MEDIA_AUDIT_WEB_PASSWORD", script)
        self.assertIn("docker compose config --quiet", script)
        self.assertIn("docker compose ps", script)
        self.assertIn("docker compose run --rm media-audit preflight", script)
        self.assertIn("--format json", script)
        self.assertNotIn("docker compose logs", script)
        self.assertNotIn("docker compose up", script)
        self.assertNotIn("docker compose build", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_stop_script_requires_confirmation_and_preserves_data(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-stop.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("--confirm", script)
        self.assertIn("explicit --confirm is required", script)
        self.assertIn("docker compose stop media-audit", script)
        self.assertIn("without removing persistent data", script)
        self.assertIn("docker compose ps", script)
        self.assertNotIn("docker compose down", script)
        self.assertNotIn("docker compose rm", script)
        self.assertNotIn("--volumes", script)
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_restart_script_is_guarded_and_reuses_safe_helpers(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-restart.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("--confirm", script)
        self.assertIn("explicit --confirm is required", script)
        self.assertIn("bash scripts/debian-vm-stop.sh --confirm", script)
        self.assertIn("bash scripts/debian-vm-start.sh", script)
        self.assertIn("without removing persistent data", script)
        self.assertIn("strict preflight", script)
        self.assertLess(
            script.index("bash scripts/debian-vm-stop.sh --confirm"),
            script.index("bash scripts/debian-vm-start.sh"),
        )
        self.assertNotIn("docker compose down", script)
        self.assertNotIn("docker compose rm", script)
        self.assertNotIn("--volumes", script)
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_backup_script_is_local_and_guarded(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-backup.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("MEDIA_AUDIT_BACKUP_DIR", script)
        self.assertIn("reports/backups", script)
        self.assertIn("--exclude='./reports/backups'", script)
        self.assertIn("data runs reports evidence", script)
        self.assertIn("media-audit-backup-", script)
        self.assertNotIn("docker compose up", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_update_script_is_guarded_and_preflighted(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-update.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("git status --porcelain --untracked-files=no", script)
        self.assertIn('[[ "${CURRENT_BRANCH}" == "main" ]]', script)
        self.assertIn("bash scripts/debian-vm-backup.sh", script)
        self.assertIn("git pull --ff-only", script)
        self.assertIn("docker compose build media-audit", script)
        self.assertIn("docker compose run --rm media-audit preflight", script)
        self.assertIn("--strict", script)
        self.assertIn("docker compose up -d", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_backup_verify_script_is_read_only(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-verify-backup.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("tar -tzf", script)
        self.assertIn("data runs reports evidence", script)
        self.assertIn("--verbose", script)
        self.assertIn("does not extract or restore data", script)
        self.assertNotIn("tar -x", script)
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("docker compose up", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_restore_preview_script_does_not_replace_live_data(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-restore-preview.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("debian-vm-verify-backup.sh", script)
        self.assertIn("reports/restore-previews", script)
        self.assertIn("refusing to extract preview over live", script)
        self.assertIn("tar -xzf", script)
        self.assertIn('-C "${PREVIEW_ROOT}"', script)
        self.assertIn("does not replace live data folders", script)
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("docker compose up", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_diagnostics_script_avoids_customer_data_and_logs(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-diagnostics.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("MEDIA_AUDIT_SUPPORT_DIR", script)
        self.assertIn("reports/support", script)
        self.assertIn("git status --short --untracked-files=no", script)
        self.assertIn("docker compose config --quiet", script)
        self.assertIn("docker compose ps", script)
        self.assertIn("docker compose run --rm media-audit preflight", script)
        self.assertIn("--format json", script)
        self.assertIn("data runs reports evidence", script)
        self.assertIn("should not contain customer data or application logs", script)
        self.assertNotIn("docker compose logs", script)
        self.assertNotIn("tar -czf", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)

    def test_debian_vm_support_bundle_packages_diagnostics_only(self) -> None:
        script = (ROOT / "scripts" / "debian-vm-support-bundle.sh").read_text(encoding="utf-8")

        self.assertIn("set -euo pipefail", script)
        self.assertIn("MEDIA_AUDIT_SUPPORT_DIR", script)
        self.assertIn("MEDIA_AUDIT_SUPPORT_BUNDLE_DIR", script)
        self.assertIn("bash scripts/debian-vm-diagnostics.sh", script)
        self.assertIn("media-audit-diagnostics-*.txt", script)
        self.assertIn("media-audit-support-", script)
        self.assertIn('tar -czf "${BUNDLE}" -C "${SUPPORT_DIR}" "${REPORT_NAME}"', script)
        self.assertIn("review before sharing", script)
        self.assertIn("not customer folders or application logs", script)
        self.assertNotIn("docker compose logs", script)
        self.assertNotIn("docker compose up", script)
        self.assertNotIn("docker compose build", script)
        self.assertNotIn("tar -czf \"${BUNDLE}\" -C \"${ROOT_DIR}\"", script)
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("apt-get", script)
        self.assertNotIn("sudo", script)
        self.assertNotIn("nmap", script)


if __name__ == "__main__":
    unittest.main()
