import os
import json
import urllib.request
import time

def test_image_scan(image_path):
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return
    
    boundary = "----WebKitFormBoundaryAutoTest"
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    filename = os.path.basename(image_path)
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(img_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/scan",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            raw_text = data.get("raw_text", "")
            lines = data.get("extracted_lines", [])
            status = data.get("overall_status")
            fields = len(data.get("fields", {}))
            print(f"[PASS] {filename:<35} | Status: {status:<15} | Lines: {len(lines):<3} | Chars: {len(raw_text):<4} | Time: {elapsed:.2f}s")
    except Exception as e:
        print(f"[FAIL] {filename:<35} | Error: {e}")

if __name__ == "__main__":
    sample_dir = "data/sample_labels"
    print("Testing /api/scan with all local sample label images:")
    for f in sorted(os.listdir(sample_dir)):
        if f.endswith((".png", ".jpg", ".jpeg")):
            test_image_scan(os.path.join(sample_dir, f))
