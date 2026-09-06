import json
import time
import sys
import os

from engine.extractor import AMCExtractor

def audit_all():
    print("=" * 80)
    print("         AUDITING ALL 50 AMC WEBSITES FOR ADDENDUM EXTRACTION")
    print("=" * 80)

    catalog_path = os.path.join(os.path.dirname(__file__), "config", "amc_catalog.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    extractor = AMCExtractor()
    
    results = []
    
    try:
        for idx, amc in enumerate(catalog, start=1):
            amc_id = amc["id"]
            name = amc["name"]
            url = amc["url"]

            print(f"[{idx:02d}/50] Testing {name[:32]:<32} ...", end=" ", flush=True)
            start_t = time.time()
            try:
                items = extractor.extract_addendums(amc)
                elapsed = time.time() - start_t
                count = len(items)
                if count > 0:
                    status = "OK"
                    sample = items[0]["doc_title"][:45]
                    print(f"[FOUND {count:2d} DOCS] ({elapsed:.1f}s) -> Sample: '{sample}'")
                else:
                    status = "ZERO_FOUND"
                    sample = ""
                    print(f"[ZERO FOUND] ({elapsed:.1f}s)")
                
                results.append({
                    "id": amc_id,
                    "name": name,
                    "url": url,
                    "status": status,
                    "count": count,
                    "sample": sample,
                    "error": None
                })
            except Exception as e:
                elapsed = time.time() - start_t
                print(f"[ERROR: {e}] ({elapsed:.1f}s)")
                results.append({
                    "id": amc_id,
                    "name": name,
                    "url": url,
                    "status": "ERROR",
                    "count": 0,
                    "sample": "",
                    "error": str(e)
                })

    finally:
        extractor.close()

    # Save audit report
    with open("audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY:")
    ok_count = sum(1 for r in results if r["status"] == "OK")
    zero_count = sum(1 for r in results if r["status"] == "ZERO_FOUND")
    err_count = sum(1 for r in results if r["status"] == "ERROR")
    print(f"  • Successfully Extracted : {ok_count} / 50")
    print(f"  • Zero Found (Needs Tuning): {zero_count} / 50")
    print(f"  • Errors (Blocked/Timeout): {err_count} / 50")
    print("=" * 80)

if __name__ == '__main__':
    audit_all()
