import unittest
from fastapi.testclient import TestClient
from main import app
from app.engine import admin_manager

class TestAdminCompliancePanel(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_admin_page(self):
        """Test that /admin returns the admin HTML page."""
        resp = self.client.get("/admin")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("MetraSetu", resp.text)
        self.assertIn("violationsTableBody", resp.text)

    def test_get_rules_api(self):
        """Test GET /api/admin/rules returns statutory rules."""
        resp = self.client.get("/api/admin/rules")
        self.assertEqual(resp.status_code, 200)
        rules = resp.json()
        self.assertIsInstance(rules, list)
        self.assertTrue(len(rules) >= 5)
        # Check presence of key rules
        rule_codes = [r.get("rule_code") for r in rules]
        self.assertTrue(any("Rule 6" in str(code) for code in rule_codes))
        self.assertTrue(any("Rule 32" in str(code) for code in rule_codes))

    def test_update_rule_api(self):
        """Test PUT /api/admin/rules/{rule_id} updates statutory parameters."""
        resp = self.client.put("/api/admin/rules/rule_6_1_e", json={
            "title": "Maximum Retail Price (MRP) Declaration - Updated",
            "section_penalty": "Section 36(1) — Fine up to ₹25,000"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("Updated", data.get("rule", {}).get("title", ""))

    def test_get_amendments_api(self):
        """Test GET /api/admin/amendments returns gazette circulars."""
        resp = self.client.get("/api/admin/amendments")
        self.assertEqual(resp.status_code, 200)
        amds = resp.json()
        self.assertIsInstance(amds, list)
        self.assertTrue(len(amds) >= 1)

    def test_add_amendment_api(self):
        """Test POST /api/admin/amendments publishes a new notification."""
        payload = {
            "notification_no": "TEST-GSR-999(E)",
            "gazette_date": "2026-08-26",
            "title": "Test Gazette Advisory on Unit Metric Fonts",
            "summary": "Testing administrative amendment publication API.",
            "authority": "Director (Legal Metrology), GoI",
            "status": "ENFORCED"
        }
        resp = self.client.post("/api/admin/amendments", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("amendment", {}).get("notification_no"), "TEST-GSR-999(E)")

    def test_get_violations_api(self):
        """Test GET /api/admin/violations returns raised non-compliant scans."""
        resp = self.client.get("/api/admin/violations")
        self.assertEqual(resp.status_code, 200)
        violations = resp.json()
        self.assertIsInstance(violations, list)

    def test_update_violation_status_api(self):
        """Test PATCH /api/admin/violations/{scan_id} updates action workflow."""
        resp = self.client.patch("/api/admin/violations/SCAN-TEST-001", json={
            "status": "DRAFT_NOTICE",
            "officer_notes": "Statutory notice drafted for Rule 32 violation."
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("action", {}).get("status"), "DRAFT_NOTICE")

    def test_admin_login_success(self):
        """Test POST /api/admin/login with valid credentials."""
        resp = self.client.post("/api/admin/login", json={
            "email": "admin@metrasetu.gov.in",
            "password": "MetraAdmin@2026"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        session = data.get("session", {})
        self.assertIn("token", session)
        self.assertEqual(session.get("email"), "admin@metrasetu.gov.in")
        self.assertEqual(session.get("name"), "Senior Metrology Officer")

    def test_admin_login_invalid_password(self):
        """Test POST /api/admin/login with invalid password fails with 401."""
        resp = self.client.post("/api/admin/login", json={
            "email": "admin@metrasetu.gov.in",
            "password": "WrongPassword123"
        })
        self.assertEqual(resp.status_code, 401)

    def test_admin_login_unknown_user(self):
        """Test POST /api/admin/login with unknown user fails with 401."""
        resp = self.client.post("/api/admin/login", json={
            "email": "unknown@random.gov.in",
            "password": "somepassword"
        })
        self.assertEqual(resp.status_code, 401)


if __name__ == '__main__':
    unittest.main()
