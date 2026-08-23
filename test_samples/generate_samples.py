import os
import shutil
from PIL import Image, ImageDraw, ImageFont

def generate_label_image(filename: str, lines: list, title: str):
    width, height = 750, 420
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(180, 190, 205), width=3)
    draw.rectangle([(16, 16), (width - 16, 54)], fill=(235, 243, 255))

    # Try font
    try:
        font_title = ImageFont.truetype("arial.ttf", 18)
        font_body = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    draw.text((26, 24), f"PACKAGED COMMODITY LABEL — {title}", fill=(20, 50, 100), font=font_title)

    y = 68
    for line in lines:
        draw.text((30, y), line, fill=(30, 40, 55), font=font_body)
        y += 26

    # Save in test_samples and data/sample_labels
    os.makedirs("test_samples", exist_ok=True)
    os.makedirs("data/sample_labels", exist_ok=True)

    out_path1 = os.path.join("test_samples", filename)
    out_path2 = os.path.join("data/sample_labels", filename)

    img.save(out_path1)
    img.save(out_path2)
    print(f"Generated sample image: {out_path1} & {out_path2}")


if __name__ == "__main__":
    # Sample 1: Fully Compliant
    generate_label_image(
        "sample1_compliant.png",
        [
            "DELUXE ALMOND KERNELS",
            "Net Wt: 250 g",
            "MRP Rs. 320.00 (Incl. of all taxes)",
            "MFD: 10/2024",
            "Manufactured & Packed by: Almond Agro Pvt Ltd, GIDC Naroda, Ahmedabad, Gujarat 382330",
            "Consumer Helpline: 1800-222-3333 | Email: care@almondagro.in"
        ],
        "COMPLIANT PRODUCT"
    )

    # Sample 2: Non-Standard Unit ("gm")
    generate_label_image(
        "sample2_non_standard_unit.png",
        [
            "SPICE MIX MASALA",
            "Net Wt: 100 gm",
            "MRP Rs. 75.00 (Incl. of all taxes)",
            "MFD: 08/2024",
            "Mfd by: Everest Spice Co, Sector 4, Mumbai 400001",
            "Customer Care: 9876543210"
        ],
        "NON-STANDARD UNIT (gm)"
    )

    # Sample 3: Dual Pricing Sticker Anomaly
    generate_label_image(
        "sample3_dual_mrp.png",
        [
            "CRUNCHY CHOCO BISCUITS 200g",
            "MRP Rs. 100.00 (Incl. of all taxes)",
            "Special Sticker Price Rs. 135.00 (revised mrp)",
            "MFD: 09/2024",
            "Packed by: Sweet Bakes Ltd, Okhla Phase 3, New Delhi 110020",
            "Consumer Helpline: care@sweetbakes.in"
        ],
        "DUAL PRICING ANOMALY"
    )

    # Sample 4: Missing Consumer Care
    generate_label_image(
        "sample4_missing_consumer_care.png",
        [
            "PURE MUSTARD OIL",
            "Net Volume: 1 L",
            "MRP Rs. 195.00",
            "MFD: 07/2024",
            "Manufactured by: Shudh Oil Mills, Industrial Area, Jaipur, Rajasthan 302013"
        ],
        "MISSING CONSUMER CARE"
    )

    # Sample 5: Exempt Bulk Package (30kg)
    generate_label_image(
        "sample5_exempt_bulk_30kg.png",
        [
            "WHOLE WHEAT FLOUR - 30 kg",
            "Not for retail sale - Institutional & Commercial Supply",
            "MRP Rs. 1150.00",
            "MFD: 06/2024",
            "Manufactured by: Bharat Flour Mills Ltd, Ludhiana 141001"
        ],
        "EXEMPT BULK (30 KG)"
    )

    # Sample 6: Small Tobacco Pack (5g - Never Exempt)
    generate_label_image(
        "sample6_tobacco_small.png",
        [
            "PREMIUM TOBACCO KHAINI",
            "Net Wt: 5 g",
            "MRP Rs. 20.00",
            "MFD: 09/2024",
            "Manufactured by: Desi Tobacco Products, Kanpur, UP 208001",
            "Consumer Helpline: 9876543210"
        ],
        "SMALL TOBACCO (5g - NOT EXEMPT)"
    )

    # Sample 7: Nutrition Panel (MUST NOT be falsely exempt despite 6g Fat / 8g Sugar)
    generate_label_image(
        "sample7_nutrition_table.png",
        [
            "PROTEIN ENERGY BARS",
            "Nutrition Information per 100g: Protein 25g, Total Fat 6g, Sugar 8g, Sodium 40mg",
            "Net Weight: 300 g",
            "MRP Rs. 240.00 (Incl. of all taxes)",
            "MFD: 10/2024",
            "Manufactured by: FitLife Foods Ltd, Whitefield, Bangalore 560066",
            "Consumer Care: 1800-444-5555 | Email: support@fitlifefoods.in"
        ],
        "NUTRITION TABLE (NOT EXEMPT)"
    )
