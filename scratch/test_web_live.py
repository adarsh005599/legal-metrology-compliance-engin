import sys
import json
import urllib.request
import urllib.parse
import os

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, method, path, data=None, headers=None):
    url = f"{BASE_URL}{path}"
    print(f"[*] Testing {name}: {method} {path} ...", end=" ")
    try:
        req_headers = headers or {}
        req_data = None
        if data:
            if isinstance(data, dict):
                req_data = json.dumps(data).encode('utf-8')
                req_headers['Content-Type'] = 'application/json'
            elif isinstance(data, bytes):
                req_data = data

        req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read()
            if status == 200:
                print(f"PASS (Status {status}, Length: {len(body)} bytes)")
                return True, body
            else:
                print(f"FAIL (Status {status})")
                return False, body
    except Exception as e:
        print(f"ERROR ({e})")
        return False, str(e)

def run_tests():
    print("=" * 70)
    print("LEGAL METROLOGY COMPLIANCE-ASSIST ENGINE — LIVE WEB TEST")
    print(f"Target Server: {BASE_URL}")
    print("=" * 70)

    results = []

    # 1. Test Static Pages
    res, body = test_endpoint("Home Scanner Page", "GET", "/")
    results.append(("Home Page", res))
    if res:
        html = body.decode('utf-8')
        assert "MetraSetu" in html
        assert "langSwitcher" in html
        assert "i18n.js" in html

    res, body = test_endpoint("Analytics Dashboard Page", "GET", "/dashboard")
    results.append(("Dashboard Page", res))
    if res:
        html = body.decode('utf-8')
        assert "MetraSetu" in html
        assert "scanSearchInput" in html

    # 2. Test Static Assets
    res, _ = test_endpoint("CSS Stylesheet", "GET", "/static/style.css")
    results.append(("style.css", res))

    res, _ = test_endpoint("i18n Localization JS", "GET", "/static/i18n.js")
    results.append(("i18n.js", res))

    res, _ = test_endpoint("App Frontend JS", "GET", "/static/app.js")
    results.append(("app.js", res))

    res, _ = test_endpoint("Dashboard JS", "GET", "/static/dashboard.js")
    results.append(("dashboard.js", res))

    res, _ = test_endpoint("Local Chart.js Bundle", "GET", "/static/chart.umd.min.js")
    results.append(("chart.umd.min.js", res))

    # 3. Test Telemetry API Endpoints
    res, body = test_endpoint("Scans Summary API", "GET", "/api/scans/summary")
    results.append(("API: /api/scans/summary", res))
    if res:
        summary = json.loads(body.decode('utf-8'))
        print(f"    -> Summary Payload: {summary}")

    res, body = test_endpoint("Recent Scans API", "GET", "/api/scans/recent")
    results.append(("API: /api/scans/recent", res))
    if res:
        recent = json.loads(body.decode('utf-8'))
        print(f"    -> Recent Scans Count: {len(recent)}")

    # 4. Test Text Scanning Endpoint (/api/scan-text)
    # Test A: Compliant Pack
    compliant_payload = {
        "text": "ORGANIC CASHEW NUTS 500g\nNet Wt: 500 g\nMRP Rs. 650.00 (incl of taxes)\nMFD: 10/2024\nManufactured by: Green Agro Foods Pvt Ltd, Ahmedabad 382330\nConsumer Care: 1800-200-4567 | care@greenagro.com",
        "filename": "demo_compliant.png"
    }
    res, body = test_endpoint("Scan Text (Compliant)", "POST", "/api/scan-text", data=compliant_payload)
    results.append(("API: /api/scan-text [Compliant]", res))
    if res:
        report = json.loads(body.decode('utf-8'))
        status = report.get('overall_status')
        print(f"    -> Overall Status: {status} (Expected: COMPLIANT)")
        assert status == "COMPLIANT"

    # Test B: Dual MRP Anomaly
    dual_mrp_payload = {
        "text": "CRUNCHY CHOCO COOKIES\nMRP Rs.20 MRPRs.25*\nMFD: 09/2024\nPacked by: Sweet Bakes Ltd, New Delhi 110020\nConsumer Helpline: 1800-222-3333",
        "filename": "demo_dual_mrp.png"
    }
    res, body = test_endpoint("Scan Text (Dual MRP)", "POST", "/api/scan-text", data=dual_mrp_payload)
    results.append(("API: /api/scan-text [Dual MRP]", res))
    if res:
        report = json.loads(body.decode('utf-8'))
        status = report.get('overall_status')
        mrp_field = next((f for f in report.get('fields', []) if 'MRP' in f.get('field_name', '')), None)
        print(f"    -> Overall Status: {status} (Expected: NON_COMPLIANT), MRP Status: {mrp_field.get('status') if mrp_field else 'N/A'}")
        assert status == "NON_COMPLIANT"
        assert mrp_field.get('status') in ("FLAGGED", "WARNING")
        assert "Rule 32(2)" in (mrp_field.get('flag') or '')

    # Test C: Statutory Bulk Exemption
    exempt_payload = {
        "text": "WHOLE WHEAT FLOUR 30 kg\nNot for retail sale - Institutional Supply\nMRP Rs. 1200.00\nMFD: 08/2024\nManufactured by: Bharat Mills Ltd",
        "filename": "demo_exempt.png"
    }
    res, body = test_endpoint("Scan Text (Exempt 30kg)", "POST", "/api/scan-text", data=exempt_payload)
    results.append(("API: /api/scan-text [Exempt]", res))
    if res:
        report = json.loads(body.decode('utf-8'))
        is_exempt = report.get('is_exempt')
        status = report.get('overall_status')
        print(f"    -> is_exempt: {is_exempt}, Status: {status} (Expected: EXEMPT)")
        assert is_exempt is True
        assert status == "EXEMPT"

    # 5. Test PDF Export Endpoint (/api/export)
    if 'report' in locals() and report:
        res, body = test_endpoint("PDF Export API", "POST", "/api/export", data=report)
        results.append(("API: /api/export", res))
        if res and isinstance(body, bytes):
            assert body.startswith(b'%PDF'), "Response must be valid PDF bytes"
            print(f"    -> Valid PDF generated ({len(body)} bytes)")

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    all_passed = True
    for name, success in results:
        status_str = "PASS" if success else "FAIL"
        print(f" - {name:.<45} [{status_str}]")
        if not success:
            all_passed = False

    if all_passed:
        print("\n>>> ALL WEB AND API ENDPOINTS VERIFIED & PASSING (100%) <<<")
        sys.exit(0)
    else:
        print("\n>>> SOME TESTS FAILED <<<")
        sys.exit(1)

if __name__ == '__main__':
    run_tests()
