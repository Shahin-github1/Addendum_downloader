import os
import sys
import json
import argparse
import datetime
import time

# Ensure Windows terminal can print safely
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from engine.date_utils import get_day_folder_name, clean_filename, get_app_root
from engine.db import StateTracker
from engine.downloader import PDFDownloader
from engine.excel_reporter import ExcelReporter
from engine.extractor import AMCExtractor

def load_catalog(catalog_path: str = None) -> list:
    if catalog_path and os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)

    app_root = get_app_root()
    # 1. Check next to executable or project root
    p1 = os.path.join(app_root, "config", "amc_catalog.json")
    if os.path.exists(p1):
        with open(p1, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2. Check in PyInstaller _internal directory
    p2 = os.path.join(app_root, "_internal", "config", "amc_catalog.json")
    if os.path.exists(p2):
        with open(p2, "r", encoding="utf-8") as f:
            return json.load(f)

    # 3. Check PyInstaller _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        p3 = os.path.join(sys._MEIPASS, "config", "amc_catalog.json")
        if os.path.exists(p3):
            with open(p3, "r", encoding="utf-8") as f:
                return json.load(f)

    raise FileNotFoundError("Could not locate config/amc_catalog.json in any expected location.")

def run_daily_download(
    amc_filter: str = None,
    limit: int = None,
    dry_run: bool = False,
    force: bool = False
):
    print("=" * 70)
    print("       Automated Indian AMC Addendum Downloader")
    print("=" * 70)

    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    day_folder = get_day_folder_name(today)

    print(f"[*] Execution Date: {today.strftime('%d-%B-%Y')}")
    print(f"[*] Target Day Folder: downloads/{day_folder}/")
    print(f"[*] Mode: {'DRY RUN (Preview Only)' if dry_run else 'LIVE DOWNLOAD'}")

    catalog = load_catalog()
    if amc_filter:
        catalog = [a for a in catalog if amc_filter.lower() in a["id"].lower() or amc_filter.lower() in a["name"].lower()]
        if not catalog:
            print(f"[!] No AMC found matching filter: '{amc_filter}'")
            return

    if limit:
        catalog = catalog[:limit]

    print(f"[*] Loaded {len(catalog)} AMC(s) to process.\n")

    tracker = StateTracker()
    downloader = PDFDownloader()
    reporter = ExcelReporter()
    extractor = AMCExtractor()

    session_records = []
    stats = {
        "total_amcs": len(catalog),
        "new_downloads": 0,
        "already_downloaded": 0,
        "no_addendums": 0,
        "errors": 0
    }

    try:
        for idx, amc in enumerate(catalog, start=1):
            amc_id = amc["id"]
            amc_name = amc["name"]
            url = amc["url"]

            print(f"[{idx}/{len(catalog)}] {amc_name} ...", end=" ", flush=True)

            try:
                candidates = extractor.extract_addendums(amc)
            except Exception as e:
                print(f"[ERROR: {e}]")
                stats["errors"] += 1
                continue

            if not candidates:
                print("[No addendums found on page]")
                stats["no_addendums"] += 1
                continue

            new_for_amc = 0
            skipped_for_amc = 0

            for doc in candidates:
                pdf_url = doc["pdf_url"]
                title = doc["doc_title"]
                date = doc["doc_date"]

                is_saved = tracker.is_downloaded(pdf_url)
                if is_saved and not force:
                    skipped_for_amc += 1
                    stats["already_downloaded"] += 1
                    continue

                # It is a new document!
                if dry_run:
                    print(f"\n      + [NEW] {title[:60]} ({date})")
                    new_for_amc += 1
                    stats["new_downloads"] += 1
                    continue

                # Download actual PDF
                res = downloader.download_file(
                    pdf_url=pdf_url,
                    amc_name=amc_name,
                    doc_title=title,
                    day_folder_name=day_folder
                )

                if res["success"]:
                    tracker.record_download(
                        amc_id=amc_id,
                        amc_name=amc_name,
                        doc_title=title,
                        doc_date=date,
                        pdf_url=pdf_url,
                        file_hash=res["file_hash"],
                        local_filename=res["file_name"],
                        local_path=res["file_path"],
                        file_size_kb=res["file_size_kb"],
                        download_date=today_str
                    )
                    session_records.append({
                        "amc_name": amc_name,
                        "doc_title": title,
                        "doc_date": date,
                        "pdf_url": pdf_url,
                        "local_filename": res["file_name"],
                        "file_size_kb": res["file_size_kb"],
                        "download_date": today.strftime("%d-%b-%Y %H:%M:%S"),
                        "status": "New Download"
                    })
                    new_for_amc += 1
                    stats["new_downloads"] += 1
                    print(f"\n      + [SAVED] {res['file_name']} ({res['file_size_kb']} KB)")
                else:
                    print(f"\n      x [DOWNLOAD FAILED] {title[:50]}: {res['error']}")
                    stats["errors"] += 1

            if new_for_amc > 0:
                print(f"Done -> {new_for_amc} new downloaded, {skipped_for_amc} already up to date.")
            else:
                print(f"Up to date -> {skipped_for_amc} existing addendums verified.")

    finally:
        extractor.close()

    # Generate Excel Report
    print("\n" + "=" * 70)
    print("Generating Excel Summary Report...")
    # Include all downloads for today recorded in DB so the Excel is comprehensive
    all_today_records = tracker.get_downloads_for_date(today_str)
    if all_today_records:
        report_records = []
        for r in all_today_records:
            report_records.append({
                "amc_name": r["amc_name"],
                "doc_title": r["doc_title"],
                "doc_date": r["doc_date"],
                "pdf_url": r["pdf_url"],
                "local_filename": r["local_filename"],
                "file_size_kb": r["file_size_kb"],
                "download_date": r["created_at"],
                "status": "Downloaded"
            })
        excel_path = reporter.generate_report(day_folder, report_records)
        print(f"[OK] Excel Report Created: {excel_path}")
    else:
        print("[*] No new downloads today; existing files remain in their respective folders.")

    # Record run in database
    tracker.record_run(
        run_date=today_str,
        total_amcs=stats["total_amcs"],
        new_downloads=stats["new_downloads"],
        skipped=stats["already_downloaded"],
        errors=stats["errors"],
        summary_json=json.dumps(stats)
    )

    print("-" * 70)
    print("EXECUTION SUMMARY:")
    print(f"  • Total AMCs Processed : {stats['total_amcs']}")
    print(f"  • New Addendums Saved  : {stats['new_downloads']}")
    print(f"  • Already Up To Date   : {stats['already_downloaded']}")
    print(f"  • Day Folder Location  : downloads/{day_folder}/")
    print("=" * 70)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Automated AMC Addendum Downloader")
    parser.add_argument("--amc", type=str, default=None, help="Filter by AMC ID or name")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of AMCs to check")
    parser.add_argument("--dry-run", action="store_true", help="Preview new addendums without downloading")
    parser.add_argument("--force", action="store_true", help="Force re-download even if already in database")
    args = parser.parse_args()

    run_daily_download(
        amc_filter=args.amc,
        limit=args.limit,
        dry_run=args.dry_run,
        force=args.force
    )
