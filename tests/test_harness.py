#!/usr/bin/env python3
"""
Automated Image Test Harness for Legal Metrology Compliance-Assist Engine
Discovers images, runs PaddleOCR and the rule engine, compares with expected_results.json,
and prints a detailed summary and field-level breakdown.

Usage:
    python tests/test_harness.py
    python tests/test_harness.py --debug
    python tests/test_harness.py tests/images/
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.engine.ocr import extract_text_from_bytes
from app.engine.exemption import check_exemptions
from app.engine.rules import evaluate_all_rules, normalize_ocr_text


def run_harness(image_dir: Path, expected_file: Path, debug: bool = False) -> int:
    print("\n" + "=" * 90)
    print(" LEGAL METROLOGY COMPLIANCE-ASSIST ENGINE — AUTOMATED IMAGE TEST HARNESS")
    print(f" Image Directory:   {image_dir}")
    print(f" Truth Ground File: {expected_file}")
    print("=" * 90 + "\n")

    if not expected_file.exists():
        print(f"[ERROR] Ground truth file not found: {expected_file}")
        return 1

    with open(expected_file, "r", encoding="utf-8") as f:
        expected_data: Dict[str, Any] = json.load(f)

    image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    image_files = sorted([p for p in image_dir.iterdir() if p.suffix.lower() in image_extensions])

    if not image_files:
        print(f"[WARNING] No image files found in {image_dir}")
        return 0

    total_images = len(image_files)
    matched_count = 0
    mismatched_count = 0
    results_summary: List[Dict[str, Any]] = []

    for img_path in image_files:
        filename = img_path.name
        expected = expected_data.get(filename, {})
        expected_overall = expected.get("overall", "UNKNOWN")
        expected_fields = expected.get("fields", {})

        print(f"Testing: {filename} ... ", end="", flush=True)

        with open(img_path, "rb") as f:
            img_bytes = f.read()

        # 1. Real OCR Pipeline
        ocr_lines, text_lines = extract_text_from_bytes(img_bytes)

        # 2. Exemption Evaluation
        exemption = check_exemptions(ocr_lines)

        # 3. Rule Evaluation
        field_results = []
        if exemption.is_exempt:
            actual_overall = "EXEMPT"
        else:
            field_results = evaluate_all_rules(ocr_lines)
            has_fail = any(f.status == "FAIL" for f in field_results)
            has_flag = any(f.status in {"WARNING", "FLAGGED"} for f in field_results)
            has_uncertain = any(f.status == "UNCERTAIN" for f in field_results)

            if has_fail or has_flag:
                actual_overall = "NON_COMPLIANT"
            elif has_uncertain:
                actual_overall = "UNCERTAIN"
            else:
                actual_overall = "COMPLIANT"

        # Check overall match
        is_overall_match = (actual_overall == expected_overall)

        # Check field-level matches
        field_matches = {}
        all_fields_matched = True
        actual_fields_map = {f.field_id: f.status for f in field_results}

        for exp_fid, exp_status in expected_fields.items():
            act_status = actual_fields_map.get(exp_fid, "N/A" if exemption.is_exempt else "NOT_FOUND")
            # Map WARNING <-> FLAGGED if interchangeable
            norm_exp = "FLAGGED" if exp_status == "WARNING" else exp_status
            norm_act = "FLAGGED" if act_status == "WARNING" else act_status
            f_match = (norm_exp == norm_act)
            field_matches[exp_fid] = {
                "expected": exp_status,
                "actual": act_status,
                "match": f_match
            }
            if not f_match:
                all_fields_matched = False

        test_passed = is_overall_match and (all_fields_matched or not expected_fields)

        if test_passed:
            matched_count += 1
            print("MATCH")
        else:
            mismatched_count += 1
            print("MISMATCH")

        results_summary.append({
            "filename": filename,
            "expected": expected_overall,
            "actual": actual_overall,
            "result": "MATCH" if test_passed else "MISMATCH",
            "field_matches": field_matches,
            "raw_lines": text_lines,
            "field_results": field_results,
            "exemption": exemption
        })

        if debug:
            print("\n" + "-" * 50)
            print(f"[DEBUG] IMAGE: {filename}")
            print(f"[DEBUG] OCR EXTRACTED LINES ({len(text_lines)}):")
            for idx, l in enumerate(text_lines):
                print(f"  {idx+1}. {l}")
            print("[DEBUG] NORMALIZED TEXT:")
            print("  " + " | ".join(normalize_ocr_text(l) for l in text_lines))
            print(f"[DEBUG] EXEMPTION: {exemption.is_exempt} (Reason: {exemption.reason})")
            print("[DEBUG] FIELD-LEVEL RESULTS:")
            for f in field_results:
                print(f"  - {f.field_name} [{f.field_id}]: {f.status} (Matched: {f.matched_text})")
                if f.flag:
                    print(f"    Flag: {f.flag}")
            print(f"[DEBUG] FINAL VERDICT: Expected={expected_overall}, Actual={actual_overall}")
            print("-" * 50 + "\n")

    # Print Summary Table
    print("\n" + "+" + "-" * 38 + "+" + "-" * 14 + "+" + "-" * 14 + "+" + "-" * 12 + "+")
    print(f"| {'Filename':<36} | {'Expected':<12} | {'Actual':<12} | {'Result':<10} |")
    print("+" + "-" * 38 + "+" + "-" * 14 + "+" + "-" * 14 + "+" + "-" * 12 + "+")
    for r in results_summary:
        print(f"| {r['filename']:<36} | {r['expected']:<12} | {r['actual']:<12} | {r['result']:<10} |")
    print("+" + "-" * 38 + "+" + "-" * 14 + "+" + "-" * 14 + "+" + "-" * 12 + "+")

    # Detailed Field-Level Breakdown for Mismatches
    mismatches = [r for r in results_summary if r["result"] == "MISMATCH"]
    if mismatches:
        print("\n" + "=" * 60)
        print(" FIELD-LEVEL MISMATCH DETAILS")
        print("=" * 60)
        for m in mismatches:
            print(f"\nFilename: {m['filename']}")
            print(f"Overall -> Expected: {m['expected']}, Actual: {m['actual']}")
            for fid, fdetail in m["field_matches"].items():
                res_str = "MATCH" if fdetail["match"] else "MISMATCH"
                print(f"  {fid}:")
                print(f"    Expected: {fdetail['expected']}")
                print(f"    Actual:   {fdetail['actual']}")
                print(f"    Result:   {res_str}")

    # Accuracy Metrics
    accuracy = (matched_count / total_images * 100) if total_images > 0 else 0.0
    print("\n" + "=" * 40)
    print(f" Images tested: {total_images}")
    print(f" Matches:       {matched_count}")
    print(f" Mismatches:    {mismatched_count}")
    print(f" Accuracy:      {accuracy:.1f}%")
    print("=" * 40 + "\n")

    return 0 if mismatched_count == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Image Test Harness")
    parser.add_argument("image_dir", nargs="?", default=str(PROJECT_ROOT / "tests" / "images"), help="Directory containing test images")
    parser.add_argument("--expected", default=str(PROJECT_ROOT / "tests" / "expected_results.json"), help="Path to expected_results.json")
    parser.add_argument("--debug", "--verbose", "-v", action="store_true", help="Enable verbose OCR debug output")
    args = parser.parse_args()

    sys.exit(run_harness(Path(args.image_dir), Path(args.expected), debug=args.debug))
