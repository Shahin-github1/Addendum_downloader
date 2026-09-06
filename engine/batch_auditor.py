import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.extractor import AMCExtractor

def run_audit(start_idx=1, end_idx=50):
    with open("config/amc_catalog.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)

    catalog = catalog[start_idx - 1: end_idx]
    extractor = AMCExtractor()

    results = []
    print("=" * 80)
    print(f" AUDITING AMCs {start_idx} to {start_idx + len(catalog) - 1} WITH STRICT ADDENDUM FILTER")
    print("=" * 80)

    try:
        for idx, amc in enumerate(catalog, start=start_idx):
            amc_id = amc["id"]
            name = amc["name"]
            url = amc["url"]

            print(f"[{idx:02d}/50] {name[:30]:<30} ...", end=" ", flush=True)
            t0 = time.time()
            try:
                items = extractor.extract_addendums(amc)
                dur = round(time.time() - t0, 1)
                count = len(items)
                if count > 0:
                    sample = items[0]["doc_title"][:40]
                    print(f"[OK: {count} Addendums] ({dur}s) -> Sample: '{sample}'")
                    status = "OK"
                else:
                    print(f"[0 Addendums] ({dur}s)")
                    status = "ZERO"
                    sample = ""
                results.append({"idx": idx, "id": amc_id, "name": name, "status": status, "count": count, "sample": sample})
            except Exception as e:
                dur = round(time.time() - t0, 1)
                print(f"[ERROR: {e}] ({dur}s)")
                results.append({"idx": idx, "id": amc_id, "name": name, "status": "ERROR", "count": 0, "sample": "", "error": str(e)})

    finally:
        extractor.close()

    report_file = f"data/audit_batch_{start_idx}_{start_idx + len(catalog) - 1}.json"
    os.makedirs("data", exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    print("-" * 80)
    print(f"Batch {start_idx}-{start_idx + len(catalog) - 1} Result: {ok_count} / {len(catalog)} extracted successfully.")
    print("=" * 80)

if __name__ == '__main__':
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    run_audit(start, end)
