import unittest
from app.models import ComplianceReport, OCRLine, MANDATORY_DISCLAIMER
from app.engine.exemption import check_exemptions
from app.engine.rules import (
    check_mrp,
    check_net_quantity,
    check_mfg_date,
    check_manufacturer_address,
    check_consumer_care,
    evaluate_all_rules,
    DUAL_MRP_REASON
)


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
        text = ["PREMIUM TOBACCO KHAINI", "Net Wt: 5 g", "MRP Rs. 10.00"]
        res = check_exemptions(text)
        self.assertFalse(res.is_exempt)

    def test_exemption_loose_goods(self):
        text = ["SWEETS", "SOLD BY WEIGHT AT COUNTER", "Price: Rs. 400/kg"]
        res = check_exemptions(text)
        self.assertTrue(res.is_exempt)
        self.assertIn("Loose / Openly-sold", res.matched_condition)

    def test_nutrition_table_does_not_trigger_false_exemption(self):
        text = [
            "PROTEIN ENERGY BARS",
            "Nutrition Information per 100g: Protein 25g, Total Fat 6g, Sugar 8g, Sodium 40mg",
            "Net Weight: 300 g",
            "MRP Rs. 240.00"
        ]
        res = check_exemptions(text)
        self.assertFalse(res.is_exempt, "Nutrition values falsely triggered small quantity exemption!")

    def test_bare_numbers_without_keyword_do_not_trigger_exemption(self):
        text = [
            "CRUNCHY CRACKERS",
            "Serving size 8g with dipping sauce",
            "Net Quantity: 200 g",
            "MRP Rs. 50.00"
        ]
        res = check_exemptions(text)
        self.assertFalse(res.is_exempt)


    # ------------------ PRIORITY 1 & 2: MRP & DUAL PRICING TESTS ------------------

    def test_mrp_valid_pass(self):
        text = ["POTATO CHIPS", "MRP Rs. 20.00 (Incl. of all taxes)"]
        res = check_mrp(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")

    def test_mrp_variants(self):
        variants = [
            "MRP Rs.20",
            "MRP Rs 20",
            "MRP: Rs.20",
            "MRP:₹20",
            "MRP ₹20",
            "MRP₹20",
            "M.R.P Rs.20",
            "M.R.P. ₹20",
            "MRP. Rs.20",
            "MRPRs.20",
            "MRP Rs. 20",
            "MRP₹20.00",
            "Maximum Retail Price Rs.20",
            "Maximum Retail Price ₹20",
            "MaximumRetailPriceRs.20",
            "MRP Rs.2O"  # OCR noise O -> 0 in price
        ]
        for v in variants:
            res = check_mrp([v])
            self.assertTrue(res.found, f"Failed to match MRP variant: {v}")
            self.assertEqual(res.status, "PASS", f"Expected PASS for variant: {v}")

    def test_mrp_missing_fail(self):
        text = ["POTATO CHIPS", "Crispy and salted snack"]
        res = check_mrp(text)
        self.assertFalse(res.found)
        self.assertEqual(res.status, "FAIL")

    def test_dual_mrp_same_line_flagged(self):
        # Master prompt explicit test case: MRP Rs.20 MRPRs.25*
        text = ["CRUNCHY BITES", "MRP Rs.20 MRPRs.25*"]
        res = check_mrp(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "FLAGGED")
        self.assertIn("Dual pricing detected", res.flag)
        self.assertIn("Rule 32(2)", res.flag)
        self.assertEqual(res.details.split(" Detected")[0], DUAL_MRP_REASON)

    def test_dual_mrp_consecutive_lines_flagged(self):
        text = ["CRUNCHY BITES", "MRP Rs. 20.00", "Special Offer MRP Rs. 25.00"]
        res = check_mrp(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "FLAGGED")
        self.assertIn(DUAL_MRP_REASON, res.flag)

    def test_duplicate_identical_mrp_not_flagged(self):
        # Identical MRP declarations should NOT be flagged as dual pricing
        text = ["MRP Rs.20", "MRP Rs.20"]
        res = check_mrp(text)
        self.assertTrue(res.found)
        self.assertEqual(res.status, "PASS")


    # ------------------ PRIORITY 2: NET QUANTITY HARDENING TESTS ------------------

    def test_net_quantity_standard_pass(self):
        cases = [
            "Net Wt 500 g",
            "Net Wt.500g",
            "Net Qty:500g",
            "Net Quantity 500 g",
            "Contains 500 g",
            "Contains:500g",
            "Contains500g"
        ]
        for c in cases:
            res = check_net_quantity([c])
            self.assertTrue(res.found, f"Failed to match: {c}")
            self.assertEqual(res.status, "PASS", f"Expected PASS for: {c}")

    def test_net_quantity_non_standard_flagged(self):
        non_std_cases = [
            "Net Wt 500 gm",
            "Net Wt 500 gms",
            "Net Wt 1 ltr",
            "Net Quantity: 2 ltrs",
            "Net Wt: 500 gm."
        ]
        for c in non_std_cases:
            res = check_net_quantity([c])
            self.assertTrue(res.found, f"Failed to match: {c}")
            self.assertEqual(res.status, "FLAGGED", f"Expected FLAGGED for: {c}")
            self.assertIn("Non-standard unit", res.flag)

    def test_net_quantity_missing_fail(self):
        text = ["BISCUITS", "Crispy snack, delicious taste"]
        res = check_net_quantity(text)
        self.assertFalse(res.found)
        self.assertEqual(res.status, "FAIL")


    # ------------------ PRIORITY 2: MFG DATE HARDENING TESTS ------------------

    def test_mfg_date_variants_pass(self):
        cases = [
            "Mfg 03/2026",
            "Mfg:03/2026",
            "Mfd 03-2026",
            "MFD: 03-2026",
            "MFG DT 03/2026",
            "Mfg Dt: 03/2026",
            "MfgDt03/2026",
            "Manufactured Mar 2026",
            "Manufactured: March 2026",
            "Packed on 03/2026",
            "Packed on 12/03/2026",
            "Packed On: 12-03-2026",
            "Pkd 03/2026"
        ]
        for c in cases:
            res = check_mfg_date([c])
            self.assertTrue(res.found, f"Failed to match mfg date: {c}")
            self.assertEqual(res.status, "PASS", f"Expected PASS for: {c}")

    def test_mfg_date_missing_fail(self):
        text = ["CANDY", "Best before 12 months", "Batch No: 998811"]
        res = check_mfg_date(text)
        self.assertFalse(res.found)
        self.assertEqual(res.status, "FAIL")


    # ------------------ PRIORITY 2: MANUFACTURER ADDRESS HARDENING TESTS ------------------

    def test_manufacturer_address_variants_pass(self):
        cases = [
            "Mfd by ABC Foods Pvt Ltd, Delhi",
            "Mfd.by: ABC Foods Pvt Ltd, Delhi",
            "Mfdby ABC Foods Pvt Ltd, Delhi",
            "Manufactured By ABC Foods Pvt Ltd, Plot 4, Okhla, New Delhi 110020",
            "ManufacturedBy ABC Foods Pvt Ltd, New Delhi",
            "Marketed By: XYZ Foods India Ltd, Mumbai 400001",
            "Packed By ABC Pvt Ltd, Jaipur 302001",
            "Distributed by ABC Distributors, Kolkata 700001"
        ]
        for c in cases:
            res = check_manufacturer_address([c])
            self.assertTrue(res.found, f"Failed to match address: {c}")
            self.assertEqual(res.status, "PASS", f"Expected PASS for: {c}")

    def test_manufacturer_address_negative_noise_fail(self):
        negative_cases = [
            ["Mfd by"],
            ["Mfd by:"],
            ["Mfd by ???"],
            ["Mfd by ----"],
            ["Mfd by 111111"],
            ["Only snack item"]
        ]
        for c in negative_cases:
            res = check_manufacturer_address(c)
            self.assertEqual(res.status, "FAIL", f"Expected FAIL for noise: {c}")


    # ------------------ PRIORITY 2: CONSUMER CARE HARDENING TESTS ------------------

    def test_consumer_care_variants_pass(self):
        cases = [
            "Customer Care: 9876543210",
            "Helpline: 98765 43210",
            "Feedback: 9876-543-210",
            "Call: 98765-43210",
            "Consumer Care: +91 9876543210",
            "Support: +91-9876543210",
            "Helpline: +919876543210",
            "Care Cell: 91 9876543210",
            "Toll Free: 1800 123 4567",
            "Toll-free Helpline: 1800-123-4567",
            "Tollfree: 18001234567",
            "Email: care@example.com",
            "Consumer Cell: care.support@example.in",
            "Feedback Email: help@company.co.in"
        ]
        for c in cases:
            res = check_consumer_care([c])
            self.assertTrue(res.found, f"Failed to match consumer care: {c}")
            self.assertEqual(res.status, "PASS", f"Expected PASS for: {c}")

    def test_consumer_care_negative_fail(self):
        negatives = [
            ["Batch 98765"],
            ["consumer@"],
            ["@example.com"],
            ["Snack product only"]
        ]
        for c in negatives:
            res = check_consumer_care(c)
            self.assertEqual(res.status, "FAIL", f"Expected FAIL for negative: {c}")


    # ------------------ OVERALL COMPLIANCE EVALUATION TESTS ------------------

    def test_standard_compliant_pack(self):
        text = [
            "ORGANIC CASHEW NUTS",
            "Net Wt: 500 g",
            "MRP Rs. 650.00 (Incl. of all taxes)",
            "MFD: 10/2024",
            "Manufactured & Packed by: Green Agro Foods Pvt Ltd, Plot 42, GIDC, Ahmedabad 382330",
            "Consumer Care Helpline: 1800-200-4567 | Email: care@greenagro.com"
        ]
        fields = evaluate_all_rules(text)
        self.assertEqual(len(fields), 5)
        self.assertTrue(all(f.status == "PASS" for f in fields))

    def test_crunchy_bites_dual_mrp_flagged(self):
        text = [
            "CRUNCHY BITES",
            "Net Wt: 200 g",
            "MRP Rs.20 / MRPRs.25*",
            "MFD: 09/2024",
            "Manufactured by: Sweet Bakes Ltd, New Delhi 110020",
            "Customer Care: 1800-111-2222"
        ]
        fields = evaluate_all_rules(text)
        mrp_field = next(f for f in fields if f.field_id == "mrp")
        self.assertEqual(mrp_field.status, "FLAGGED")
        self.assertIn("Dual pricing detected", mrp_field.flag)


if __name__ == "__main__":
    unittest.main()
