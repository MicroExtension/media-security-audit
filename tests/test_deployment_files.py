from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeploymentFileTests(unittest.TestCase):
    def test_dockerfile_uses_non_root_user_and_local_web_command(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("apt-get install -y --no-install-recommends", dockerfile)
        self.assertIn("nmap", dockerfile)
        self.assertIn("USER mediaaudit", dockerfile)
        self.assertIn("/var/lib/media-audit/data", dockerfile)
        self.assertIn('"--host", "0.0.0.0"', dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)

    def test_compose_defaults_to_localhost_and_persistent_volumes(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("${MEDIA_AUDIT_BIND:-127.0.0.1}:${MEDIA_AUDIT_PORT:-8080}:8080", compose)
        self.assertIn("./data:/var/lib/media-audit/data", compose)
        self.assertIn("./runs:/var/lib/media-audit/runs", compose)
        self.assertIn("./reports:/var/lib/media-audit/reports", compose)
        self.assertIn("./evidence:/var/lib/media-audit/evidence", compose)
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


if __name__ == "__main__":
    unittest.main()
