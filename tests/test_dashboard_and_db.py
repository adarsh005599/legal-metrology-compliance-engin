import unittest
from fastapi.testclient import TestClient

from main import app
from app.models import ComplianceReport, MANDATORY_DISCLAIMER
from app.engine.rules import evaluate_all_rules
from app.db.supabase_client import save_scan_record, get_scans_summary, get_recent_scans, _memory_scans


class TestDashboardAndDatabase(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_save_scan_record_and_summary(self):
        # Initial count
        init_summary = get_scans_summary()
        init_total = init_summary.get("total", 0)

        # Create a sample compliant report
        text = [
            "ORGANIC CASHEWS",
            "Net Wt: 500 g",
            "MRP Rs. 650.00",
            "MFD: 10/2024",
            "Manufactured by: Agro Ltd, Pune",
            "Consumer Care: 1800-111-2222"
        ]
        fields = evaluate_all_rules(text)
        report = ComplianceReport(
            scan_id="LM-TEST-SCAN-1",
            timestamp="23-08-2026 23:00:00 IST",
            filename="sample_cashew.png",
            is_exempt=False,
            overall_status="COMPLIANT",
            fields=fields,
            raw_text="\n".join(text),
            disclaimer=MANDATORY_DISCLAIMER
        )

        res = save_scan_record(report)
        self.assertTrue(res)

        summary = get_scans_summary()
        self.assertGreaterEqual(summary["total"], init_total + 1)
        self.assertGreaterEqual(summary["compliant"], 1)

        recent = get_recent_scans(limit=10)
        self.assertGreaterEqual(len(recent), 1)
        self.assertEqual(recent[0]["scan_ref_id"], "LM-TEST-SCAN-1")

    def test_api_scans_summary_endpoint(self):
        res = self.client.get("/api/scans/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total", data)
        self.assertIn("compliant", data)
        self.assertIn("non_compliant", data)
        self.assertIn("exempt", data)

    def test_api_scans_recent_endpoint(self):
        # Add a scan through /api/scan-text
        payload = {
            "text": "NATURAL CARDAMOM\nNet Wt: 5 g\nMRP Rs. 10.00\nMFD: 10/2024\nMfd by: Fresh Herbs Ltd",
            "filename": "small_cardamom.png"
        }
        scan_res = self.client.post("/api/scan-text", json=payload)
        self.assertEqual(scan_res.status_code, 200)
        report = scan_res.json()
        self.assertTrue(report["is_exempt"])

        recent_res = self.client.get("/api/scans/recent")
        self.assertEqual(recent_res.status_code, 200)
        recent_list = recent_res.json()
        self.assertGreaterEqual(len(recent_list), 1)
        self.assertEqual(recent_list[0]["status"], "exempt")

    def test_dashboard_route_serves_html(self):
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))
        self.assertIn("Analytics Dashboard", res.text)


if __name__ == "__main__":
    unittest.main()
