import os
import sys
import csv
import glob
from typing import List, Dict, Any

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.engine.ocr import extract_text_from_bytes
from app.engine.exemption import check_exemptions
from app.engine.rules import evaluate_all_rules


def run_batch_test(directory_path: str = "data/sample_labels", output_csv: str = "batch_test_results.csv"):
    """
    Internal batch test script that processes all label images in a directory
    through the complete compliance screening pipeline and outputs a summary table.
    """
    # Check directory
    if not os.path.exists(directory_path) or not os.listdir(directory_path):
        fallback = "test_samples"
        if os.path.exists(fallback) and os.listdir(fallback):
            print(f"[INFO] '{directory_path}' not found or empty. Using '{fallback}' instead.")
            directory_path = fallback
        else:
            print(f"[ERROR] No images found in '{directory_path}' or '{fallback}'.")
            return

    image_extensions = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(glob.glob(os.path.join(directory_path, ext)))

    image_paths = sorted(image_paths)
    if not image_paths:
        print(f"[ERROR] No image files found in {directory_path}.")
        return

    print(f"\n==================================================================================")
    print(f" LEGAL METROLOGY COMPLIANCE-ASSIST ENGINE — BATCH SELF-TEST SUITE")
    print(f" Target Directory: {directory_path} ({len(image_paths)} images)")
    print(f"==================================================================================\n")

    results: List[Dict[str, Any]] = []

    for img_path in image_paths:
        filename = os.path.basename(img_path)
        print(f"Processing: {filename} ...", end=" ", flush=True)

        try:
            with open(img_path, "rb") as f:
                image_bytes = f.read()

            ocr_lines, text_lines = extract_text_from_bytes(image_bytes)
            exemption = check_exemptions(ocr_lines)

            row: Dict[str, Any] = {
                "Filename": filename,
                "Lines_Detected": len(ocr_lines),
                "Exempt": "YES" if exemption.is_exempt else "NO",
                "Exemption_Reason": exemption.matched_condition or "None",
                "MRP": "N/A (Exempt)" if exemption.is_exempt else "FAIL",
                "MRP_Conf": "-",
                "Net_Qty": "N/A (Exempt)" if exemption.is_exempt else "FAIL",
                "Net_Qty_Conf": "-",
                "Mfg_Date": "N/A (Exempt)" if exemption.is_exempt else "FAIL",
                "Mfg_Date_Conf": "-",
                "Address": "N/A (Exempt)" if exemption.is_exempt else "FAIL",
                "Address_Conf": "-",
                "Consumer_Care": "N/A (Exempt)" if exemption.is_exempt else "FAIL",
                "Consumer_Care_Conf": "-",
                "Overall_Status": "EXEMPT" if exemption.is_exempt else "FAIL"
            }

            if not exemption.is_exempt:
                fields = evaluate_all_rules(ocr_lines)
                field_map = {f.field_id: f for f in fields}

                # MRP
                if "mrp" in field_map:
                    f = field_map["mrp"]
                    row["MRP"] = f.status
                    row["MRP_Conf"] = f"{int(f.confidence_score*100)}%" if f.confidence_score is not None else "-"

                # Net Qty
                if "net_quantity" in field_map:
                    f = field_map["net_quantity"]
                    row["Net_Qty"] = f.status
                    row["Net_Qty_Conf"] = f"{int(f.confidence_score*100)}%" if f.confidence_score is not None else "-"

                # Mfg Date
                if "mfg_date" in field_map:
                    f = field_map["mfg_date"]
                    row["Mfg_Date"] = f.status
                    row["Mfg_Date_Conf"] = f"{int(f.confidence_score*100)}%" if f.confidence_score is not None else "-"

                # Address
                if "address" in field_map:
                    f = field_map["address"]
                    row["Address"] = f.status
                    row["Address_Conf"] = f"{int(f.confidence_score*100)}%" if f.confidence_score is not None else "-"

                # Consumer Care
                if "consumer_care" in field_map:
                    f = field_map["consumer_care"]
                    row["Consumer_Care"] = f.status
                    row["Consumer_Care_Conf"] = f"{int(f.confidence_score*100)}%" if f.confidence_score is not None else "-"

                has_failure = any(f.status == "FAIL" for f in fields)
                has_warning = any(f.status == "WARNING" for f in fields)
                has_uncertain = any(f.status == "UNCERTAIN" for f in fields)

                if has_failure or has_warning:
                    row["Overall_Status"] = "NON_COMPLIANT"
                elif has_uncertain:
                    row["Overall_Status"] = "UNCERTAIN"
                else:
                    row["Overall_Status"] = "COMPLIANT"

            results.append(row)
            print(f"Done [{row['Overall_Status']}]")

        except Exception as e:
            print(f"Error: {e}")
            results.append({
                "Filename": filename,
                "Lines_Detected": 0,
                "Exempt": "ERROR",
                "Exemption_Reason": str(e),
                "MRP": "ERROR",
                "MRP_Conf": "-",
                "Net_Qty": "ERROR",
                "Net_Qty_Conf": "-",
                "Mfg_Date": "ERROR",
                "Mfg_Date_Conf": "-",
                "Address": "ERROR",
                "Address_Conf": "-",
                "Consumer_Care": "ERROR",
                "Consumer_Care_Conf": "-",
                "Overall_Status": "ERROR"
            })

    # Print Summary Table
    print("\n" + "="*115)
    header_fmt = "{:<32} {:<8} {:<10} {:<10} {:<10} {:<10} {:<15} {:<14}"
    print(header_fmt.format("FILENAME", "EXEMPT", "MRP", "NET_QTY", "MFG_DATE", "ADDRESS", "CONSUMER_CARE", "OVERALL"))
    print("="*115)

    for r in results:
        print(header_fmt.format(
            r["Filename"][:30],
            r["Exempt"],
            f"{r['MRP']} ({r['MRP_Conf']})" if r['MRP_Conf'] != '-' else r['MRP'],
            f"{r['Net_Qty']} ({r['Net_Qty_Conf']})" if r['Net_Qty_Conf'] != '-' else r['Net_Qty'],
            f"{r['Mfg_Date']} ({r['Mfg_Date_Conf']})" if r['Mfg_Date_Conf'] != '-' else r['Mfg_Date'],
            f"{r['Address']} ({r['Address_Conf']})" if r['Address_Conf'] != '-' else r['Address'],
            f"{r['Consumer_Care']} ({r['Consumer_Care_Conf']})" if r['Consumer_Care_Conf'] != '-' else r['Consumer_Care'],
            r["Overall_Status"]
        ))
    print("="*115 + "\n")

    # Write CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"[SUCCESS] Batch test results written to: {output_csv}\n")


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "data/sample_labels"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "batch_test_results.csv"
    run_batch_test(target_dir, out_file)
