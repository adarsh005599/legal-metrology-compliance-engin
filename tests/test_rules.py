import unittest
from app.models import ComplianceReport, OCRLine, MANDATORY_DISCLAIMER
from app.engine.exemption import check_exemptions
from app.engine.rules import (
    check_mrp,
    check_net_quantity,
    check_mfg_date,
    check_manufacturer_address,
    check_consumer_care,
    evaluate_all_rules
)
from app.engine.pdf_report import generate_pdf_report


class TestLegalMetrologyRules(unittest.TestCase):

    # ------------------ EXEMPTION FILTER TESTS ------------------

    def test_exemption_not_for_retail_sale(self):
        text = ["BULK TEA", "NOT FOR RETAIL SALE", "Institutional supply only", "Weight: 10 kg"]
        res = check_exemptions(text)
        self.assertTrue(res.is_exempt)
        self.assertIn("Not for retail sale", res.matched_condition)

    def test_exemption_weight_over_25kg_standard(self):
        text = ["WHOLE WHEAT FLOUR", "Net Weight: 30 kg", "MRP Rs. 1200", "MFD: 06/2024"]
        res = check_exemptions(text)
        self.assertTrue(res.is_exempt)
        self.assertIn("exceeds maximum weight", res.matched_condition)

    def test_non_exemption_weight_under_25kg(self):
        text = ["WHOLE WHEAT FLOUR", "Net Weight: 10 kg", "MRP Rs. 450", "MFD: 06/2024"]
        res = check_exemptions(text)
        self.assertFalse(res.is_exempt)

    def test_exemption_cement_fertilizer_over_50kg(self):
        # 40kg cement is NOT exempt (threshold is 50kg for cement/fertiliser)
        text_40kg = ["PORTLAND CEMENT", "Net Weight: 40 kg", "MRP Rs. 380"]
        res_40kg = check_exemptions(text_40kg)
        self.assertFalse(res_40kg.is_exempt)

        # 60kg cement IS exempt (> 50kg)
        text_60kg = ["PORTLAND CEMENT", "Net Weight: 60 kg", "MRP Rs. 550"]
        res_60kg = check_exemptions(text_60kg)
        self.assertTrue(res_60kg.is_exempt)

    def test_exemption_small_package_non_tobacco(self):
        text = ["HERBAL MOUTH FRESHENER", "Net Wt: 5 g", "MRP Rs. 5.00"]
        res = check_exemptions(text)
        self.assertTrue(res.is_exempt)
        self.assertIn("Small package exemption", res.matched_condition)

    def test_exemption_small_package_tobacco_is_never_exempt(self):
        # Tobacco products are never exempt even if <= 10g
        text = ["PREMIUM TOBACCO KHAINI", "Net Wt: 5 g", "MRP Rs. 10.00"]
        res = check_exemptions(text)
        self.assertFalse(res.is_exempt)

    def test_exemption_loose_goods(self):
        text = ["SWEETS", "SOLD BY WEIGHT AT COUNTER", "Price: Rs. 400/kg"]
        res = check_exemptions(text)
        self.assertTrue(res.is_exempt)
        self.assertIn("Loose / Openly-sold", res.matched_condition)

    def test_nutrition_table_does_not_trigger_false_exemption(self):
        # High priority bug fix test: Nutrition panel with numbers <=10g (Protein 25g, Fat 6g, Sugar 8g)
        # must NOT trigger exemption when declared net weight is 300g
        text = [
            "PROTEIN ENERGY BARS",
            "Nutrition Information per 100g: Protein 25g, Total Fat 6g, Sugar 8g, Sodium 40mg",
            "Net Weight: 300 g",
            "MRP Rs. 240.00"
        ]
        res = check_exemptions(text)
        self.assertFalse(res.is_exempt, "Nutrition values falsely triggered small quantity exemption!")

    def test_bare_numbers_without_keyword_do_not_trigger_exemption(self):
        # Bare numbers without "net wt" or "contains" should not trigger small qty exemption
        text = [
            "CRUNCHY CRACKERS",
            "Serving size 8g with dipping sauce",
            "Net Quantity: 200 g",
            "MRP Rs. 50.00"
        ]
        res = check_exemptions(text)
        self.assertFalse(res.is_exempt)


    # ------------------ RULE 1: MRP TESTS ------------------

    def test_mrp_valid_pass(self):
        text = ["POTATO CHIPS", "MRP Rs. 20.00 (Incl. of all taxes)"]
        res = check_mrp(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")
        self.assertIsNone(res.flag)

    def test_mrp_missing_fail(self):
        text = ["POTATO CHIPS", "Crispy and salted snack"]
        res = check_mrp(text)
        self.assertFalse(res.found)
        self.assertEqual(res.status, "FAIL")

    def test_mrp_dual_pricing_anomaly_flagged(self):
        text = ["POTATO CHIPS", "MRP Rs. 20.00", "Special sticker price Rs. 25.00 (revised mrp)"]
        res = check_mrp(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "WARNING")
        self.assertIsNotNone(res.flag)
        self.assertIn("Dual Pricing", res.flag)


    # ------------------ RULE 2: NET QUANTITY TESTS ------------------

    def test_net_quantity_standard_si_pass(self):
        text = ["CHOCOLATE BAR", "Net Quantity: 150 g"]
        res = check_net_quantity(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")
        self.assertIsNone(res.flag)

    def test_net_quantity_non_standard_unit_flagged(self):
        text = ["SPICE PACK", "Net Weight: 200 gm"]
        res = check_net_quantity(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "WARNING")
        self.assertIsNotNone(res.flag)
        self.assertIn("Non-standard unit", res.flag)

    def test_net_quantity_missing_fail(self):
        text = ["SPICE PACK", "Authentic Indian Spices"]
        res = check_net_quantity(text)
        self.assertFalse(res.found)
        self.assertEqual(res.status, "FAIL")

    def test_net_quantity_ignores_nutrition_panel(self):
        # Must extract 400 g from "Net Wt: 400 g", not "Fat 5g" from nutrition table
        text = [
            "CORN FLAKES",
            "Nutrition per 100g: Protein 7g, Total Fat 2g, Dietary Fiber 3g",
            "Net Weight: 400 g",
            "MRP Rs. 160.00"
        ]
        res = check_net_quantity(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")
        self.assertIn("400 g", res.matched_text)


    # ------------------ RULE 3: MFG / PACKING DATE TESTS ------------------

    def test_mfg_date_valid_pass(self):
        for pattern in [
            "MFD: 10/2024",
            "Pkd on: 15/08/2024",
            "Date of Mfg: OCT 2024",
            "Manufactured: 05-2024",
            "PKD: 09/24"
        ]:
            text = ["SAMPLE COMMODITY", pattern]
            res = check_mfg_date(text)
            self.assertTrue(res.found, f"Failed to match date pattern: {pattern}")
            self.assertEqual(res.status, "PASS")

    def test_mfg_date_missing_fail(self):
        text = ["SAMPLE COMMODITY", "Best before 6 months from date"]
        res = check_mfg_date(text)
        self.assertFalse(res.found)
        self.assertEqual(res.status, "FAIL")


    # ------------------ RULE 4: MANUFACTURER ADDRESS TESTS ------------------

    def test_manufacturer_address_valid_pass(self):
        text = [
            "ALMOND OIL",
            "Manufactured & Packed by: Apex Consumer Products Ltd, Plot 12, GIDC, Vapi, Gujarat 396195"
        ]
        res = check_manufacturer_address(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")

    def test_manufacturer_address_missing_fail(self):
        text = ["ALMOND OIL", "Pure and 100% natural"]
        res = check_manufacturer_address(text)
        self.assertFalse(res.found)
        self.assertEqual(res.status, "FAIL")


    # ------------------ RULE 5: CONSUMER CARE DETAILS TESTS ------------------

    def test_consumer_care_phone_pass(self):
        text = ["FRUIT JUICE", "Customer Care: 9876543210"]
        res = check_consumer_care(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")

    def test_consumer_care_tollfree_pass(self):
        text = ["FRUIT JUICE", "Consumer Helpline Toll Free: 1800-200-9999"]
        res = check_consumer_care(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")

    def test_consumer_care_email_pass(self):
        text = ["FRUIT JUICE", "Reach us at feedback@tastegood.in for queries"]
        res = check_consumer_care(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")

    def test_consumer_care_missing_fail(self):
        text = ["FRUIT JUICE", "Tasty & refreshing drink"]
        res = check_consumer_care(text)
        self.assertFalse(res.found)
        self.assertEqual(res.status, "FAIL")


    # ------------------ CONFIDENCE-BASED REJECTION TESTS ------------------

    def test_confidence_rejection_low_confidence_marks_uncertain(self):
        # Line with confidence 0.45 (< 0.60) must be marked UNCERTAIN
        ocr_lines = [
            OCRLine(text="ENERGY COOKIES", confidence=0.95),
            OCRLine(text="MRP Rs. 50.00", confidence=0.45), # Low confidence (< 0.60)
            OCRLine(text="Net Wt: 200 g", confidence=0.92),
            OCRLine(text="MFD: 10/2024", confidence=0.95),
            OCRLine(text="Manufactured by: Bakery Ltd, Delhi", confidence=0.90),
            OCRLine(text="Helpline: 9876543210", confidence=0.91),
        ]

        mrp_res = check_mrp(ocr_lines)
        self.assertTrue(mrp_res.found)
        self.assertEqual(mrp_res.status, "UNCERTAIN")
        self.assertEqual(mrp_res.confidence_score, 0.45)
        self.assertIn("Uncertain — low OCR confidence", mrp_res.details)

    def test_confidence_pass_high_confidence_marks_pass(self):
        # Line with confidence 0.92 (>= 0.60) must be marked PASS
        ocr_lines = [
            OCRLine(text="MRP Rs. 50.00", confidence=0.92),
        ]
        mrp_res = check_mrp(ocr_lines)
        self.assertTrue(mrp_res.found)
        self.assertEqual(mrp_res.status, "PASS")
        self.assertEqual(mrp_res.confidence_score, 0.92)


    # ------------------ PDF GENERATION TESTS ------------------

    def test_pdf_generation_compliant_report(self):
        text = [
            "PREMIUM CASHEWS",
            "Net Wt: 500 g",
            "MRP Rs. 650.00 (Incl. of all taxes)",
            "MFD: 10/2024",
            "Manufactured by: Green Foods Ltd, Pune 411001",
            "Consumer Care: 1800-111-2222"
        ]
        fields = evaluate_all_rules(text)
        report = ComplianceReport(
            scan_id="LM-TEST-001",
            timestamp="23-08-2026 21:00:00 IST",
            filename="test_label.jpg",
            is_exempt=False,
            overall_status="COMPLIANT",
            fields=fields,
            raw_text="\n".join(text),
            disclaimer=MANDATORY_DISCLAIMER
        )

        pdf_bytes = generate_pdf_report(report)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_pdf_generation_uncertain_report(self):
        # PDF test with UNCERTAIN status
        ocr_lines = [
            OCRLine(text="MRP Rs. 50.00", confidence=0.48),
            OCRLine(text="Net Wt: 200 g", confidence=0.90),
            OCRLine(text="MFD: 10/2024", confidence=0.91),
            OCRLine(text="Manufactured by: Food Corp", confidence=0.92),
            OCRLine(text="Helpline: 9876543210", confidence=0.93),
        ]
        fields = evaluate_all_rules(ocr_lines)
        report = ComplianceReport(
            scan_id="LM-TEST-UNCERTAIN",
            timestamp="23-08-2026 21:00:00 IST",
            filename="noisy_scan.jpg",
            is_exempt=False,
            overall_status="UNCERTAIN",
            fields=fields,
            extracted_lines=ocr_lines,
            raw_text="noisy text",
            disclaimer=MANDATORY_DISCLAIMER
        )

        pdf_bytes = generate_pdf_report(report)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
