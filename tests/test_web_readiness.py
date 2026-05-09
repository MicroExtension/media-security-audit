from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from media_security_audit.models import (  # noqa: E402
    Finding,
    FindingStatus,
    Mission,
    ScopeItem,
    ScopeType,
    Severity,
)
from media_security_audit.web_readiness import (  # noqa: E402
    build_readiness_items,
    build_scan_plan_previews,
)


class WebReadinessTests(unittest.TestCase):
    def test_blocks_missing_authorization_and_scope(self) -> None:
        mission = Mission(client_id="client_1", name="Audit")

        items = build_readiness_items(mission, findings=[], generated_report_count=0)
        statuses = {item.label: item.status for item in items}

        self.assertEqual(statuses["Authorization"], "blocked")
        self.assertEqual(statuses["Approved Scope"], "blocked")
        self.assertEqual(statuses["Finding Review"], "warning")
        self.assertEqual(statuses["Reports"], "warning")

    def test_marks_reviewed_findings_and_reports_ready(self) -> None:
        mission = Mission(
            client_id="client_1",
            name="Audit",
            authorization_reference="AUTH-001",
            scope=[ScopeItem(type=ScopeType.IP, value="192.0.2.10", approved=True)],
        )
        finding = Finding(
            title="Reviewed finding",
            severity=Severity.LOW,
            affected_asset="192.0.2.10",
            category="network",
            source_module="manual",
            proof="Manual evidence.",
            risk="Risk under review.",
            remediation="Apply remediation.",
            counter_test="Repeat the approved check.",
            confidence=0.8,
            status=FindingStatus.CONFIRMED,
        )

        items = build_readiness_items(mission, findings=[finding], generated_report_count=3)
        statuses = {item.label: item.status for item in items}

        self.assertEqual(statuses["Authorization"], "ready")
        self.assertEqual(statuses["Approved Scope"], "ready")
        self.assertEqual(statuses["Finding Review"], "ready")
        self.assertEqual(statuses["Reports"], "ready")

    def test_builds_safe_scan_plan_previews_from_approved_scope(self) -> None:
        mission = Mission(
            client_id="client_1",
            name="Audit",
            authorization_reference="AUTH-001",
            scope=[
                ScopeItem(type=ScopeType.IP, value="192.0.2.10", approved=True),
                ScopeItem(type=ScopeType.URL, value="https://client.example", approved=True),
                ScopeItem(type=ScopeType.DOMAIN, value="client.example", approved=True),
            ],
        )

        plans = {plan.label: plan for plan in build_scan_plan_previews(mission)}

        self.assertEqual(plans["Nmap"].status, "ready")
        self.assertTrue(any(command.startswith("nmap -sV") for command in plans["Nmap"].commands))
        self.assertEqual(plans["HTTP Headers"].commands, ["HEAD/GET https://client.example"])
        self.assertEqual(plans["DNS/Mail"].commands, ["TXT client.example", "TXT _dmarc.client.example"])

    def test_blocks_unavailable_scan_plan_previews(self) -> None:
        mission = Mission(client_id="client_1", name="Audit")

        plans = {plan.label: plan for plan in build_scan_plan_previews(mission)}

        self.assertEqual(plans["Nmap"].status, "blocked")
        self.assertEqual(plans["HTTP Headers"].status, "blocked")
        self.assertEqual(plans["DNS/Mail"].status, "blocked")
        self.assertEqual(plans["Nmap"].commands, [])


if __name__ == "__main__":
    unittest.main()
