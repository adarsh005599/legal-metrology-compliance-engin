import os
import unittest
from app.engine.ocr import extract_text_from_bytes
from app.engine.exemption import check_exemptions
from app.engine.rules import evaluate_all_rules
from app.engine.pdf_report import generate_pdf_report
from app.models import ComplianceReport, MANDATORY_DISCLAIMER

class TestEndToEndPipeline(unittest.TestCase):

    def run_image_pipeline(self, image_path: str) -> ComplianceReport:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ocr_lines, text_lines = extract_text_from_bytes(image_bytes)
        exemption = check_exemptions(text_lines)

        if exemption.is_exempt:
            report = ComplianceReport(
                scan_id="LM-TEST-EXEMPT",
                timestamp="23-08-2026 22:00:00 IST",
                filename=os.path.basename(image_path),
                is_exempt=True,
                exemption_details=exemption,
                overall_status="EXEMPT",
                fields=[],
                extracted_lines=ocr_lines,
                raw_text="\n".join(text_lines),
                disclaimer=MANDATORY_DISCLAIMER
            )
        else:
            fields = evaluate_all_rules(text_lines)
            has_fail = any(f.status == "FAIL" for f in fields)
            has_warn = any(f.status == "WARNING" for f in fields)
            overall_status = "NON_COMPLIANT" if (has_fail or has_warn) else "COMPLIANT"

            report = ComplianceReport(
                scan_id="LM-TEST-SCAN",
                timestamp="23-08-2026 22:00:00 IST",
                filename=os.path.basename(image_path),
                is_exempt=False,
                overall_status=overall_status,
                fields=fields,
                extracted_lines=ocr_lines,
                raw_text="\n".join(text_lines),
                disclaimer=MANDATORY_DISCLAIMER
            )

        pdf_bytes = generate_pdf_report(report)
        self.assertGreater(len(pdf_bytes), 1000)
        return report

    def test_sample1_compliant(self):
        report = self.run_image_pipeline("test_samples/sample1_compliant.png")
        self.assertFalse(report.is_exempt)
        self.assertEqual(report.overall_status, "COMPLIANT")
        self.assertEqual(len(report.fields), 5)
        for f in report.fields:
            self.assertTrue(f.found, f"Expected field {f.field_name} to be found")

    def test_sample2_non_standard_unit(self):
        report = self.run_image_pipeline("test_samples/sample2_non_standard_unit.png")
        self.assertFalse(report.is_exempt)
        self.assertEqual(report.overall_status, "NON_COMPLIANT")
        # Net quantity must be flagged for "gm"
        net_qty = next(f for f in report.fields if f.field_id == "net_quantity")
        self.assertTrue(net_qty.found)
        self.assertEqual(net_qty.status, "WARNING")
        self.assertIn("Non-standard unit", net_qty.flag)

    def test_sample3_dual_mrp(self):
        report = self.run_image_pipeline("test_samples/sample3_dual_mrp.png")
        self.assertFalse(report.is_exempt)
        mrp_field = next(f for f in report.fields if f.field_id == "mrp")
        self.assertTrue(mrp_field.found)
        self.assertEqual(mrp_field.status, "WARNING")
        self.assertIn("Dual Pricing", mrp_field.flag)

    def test_sample4_missing_consumer_care(self):
        report = self.run_image_pipeline("test_samples/sample4_missing_consumer_care.png")
        self.assertFalse(report.is_exempt)
        care_field = next(f for f in report.fields if f.field_id == "consumer_care")
        self.assertFalse(care_field.found)
        self.assertEqual(care_field.status, "FAIL")

    def test_sample5_exempt_bulk(self):
        report = self.run_image_pipeline("test_samples/sample5_exempt_bulk_30kg.png")
        self.assertTrue(report.is_exempt)
        self.assertEqual(report.overall_status, "EXEMPT")
        self.assertIsNotNone(report.exemption_details)

    def test_sample6_tobacco_small_not_exempt(self):
        report = self.run_image_pipeline("test_samples/sample6_tobacco_small.png")
        # Tobacco <= 10g is NOT exempt under Rule 26
        self.assertFalse(report.is_exempt)
        self.assertEqual(report.overall_status, "COMPLIANT")

if __name__ == "__main__":
    unittest.main()
