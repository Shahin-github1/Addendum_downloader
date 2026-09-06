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

from engine.date_utils import get_day_folder_name, clean_filename, get_app_root, parse_flexible_date, is_date_on_or_after
from engine.excel_tracker import ExcelTracker
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

def import_folder_into_tracker(folder_path: str):
    """Recursively scans an existing folder of PDFs and registers them into Excel Master Tracker."""
    if not os.path.exists(folder_path):
        print(f"[!] Folder not found: {folder_path}")
        return

    print("=" * 70)
    print(f"Importing Existing PDFs into Excel Master Tracker")
    print(f"Target Directory: {folder_path}")
    print("=" * 70)

    tracker = ExcelTracker()
    count = 0
    skipped = 0

    for root, dirs, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(".pdf"):
                full_p = os.path.join(root, f)
                # Infer AMC name from parent directory name or filename
                parent_dir = os.path.basename(root)
                amc_name = parent_dir if parent_dir not in ["downloads", ".", ""] else "Existing Addendum"
                
                success = tracker.import_local_file(
                    file_path=full_p,
                    amc_name=amc_name,
                    doc_title=os.path.splitext(f)[0]
                )
                if success:
                    count += 1
                    print(f"  + [REGISTERED] {f} ({amc_name})")
                else:
                    skipped += 1

    print("-" * 70)
    print(f"[OK] Import Complete: {count} new files registered into Excel Master Tracker.")
    print(f"    ({skipped} files were already indexed or invalid)")
    print(f"Master Tracker Location: {tracker.tracker_path}")
    print("=" * 70)

def run_daily_download(
    amc_filter: str = None,
    limit: int = None,
    from_date_str: str = None,
    dry_run: bool = False,
    force: bool = False
):
    print("=" * 70)
    print("       Automated Indian AMC Addendum Downloader")
    print("=" * 70)

    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    day_folder = get_day_folder_name(today)

    cutoff_date = None
    if from_date_str:
        cutoff_date = parse_flexible_date(from_date_str)
        if cutoff_date:
            print(f"[*] Date Filter Active: Only addendums on/after {cutoff_date.strftime('%d-%b-%Y')}")
        else:
            print(f"[!] Warning: Could not parse --from-date '{from_date_str}'. Proceeding without date filter.")

    print(f"[*] Execution Date: {today.strftime('%d-%B-%Y')}")
    print(f"[*] Target Day Folder: downloads/{day_folder}/")
    print(f"[*] Master Excel Tracker: data/addendum_master_tracker.xlsx")
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

    tracker = ExcelTracker()
    downloader = PDFDownloader()
    reporter = ExcelReporter()
    extractor = AMCExtractor()

    session_records = []
    stats = {
        "total_amcs": len(catalog),
        "new_downloads": 0,
        "already_downloaded": 0,
        "filtered_by_date": 0,
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
                candidates = extractor.extract_addendums(amc, from_date=cutoff_date)
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

                # 1. Date Range Filtering
                if cutoff_date and date:
                    if not is_date_on_or_after(date, cutoff_date):
                        stats["filtered_by_date"] += 1
                        continue

                # 2. Extract original filename and check deduplication
                expected_orig_name = downloader.extract_original_filename(pdf_url, fallback_title=title)
                is_saved = tracker.is_downloaded(pdf_url, filename=expected_orig_name, amc_name=amc_name)
                if is_saved and not force:
                    skipped_for_amc += 1
                    stats["already_downloaded"] += 1
                    continue

                # It is a new document!
                if dry_run:
                    print(f"\n      + [NEW] {expected_orig_name} ({date})")
                    new_for_amc += 1
                    stats["new_downloads"] += 1
                    continue

                # Download actual PDF preserving original filename
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
                        download_date=today_str,
                        status="Downloaded"
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

    # Generate Daily Excel Report
    print("\n" + "=" * 70)
    print("Generating Daily Excel Summary Report...")
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
                "status": r.get("status", "Downloaded")
            })
        excel_path = reporter.generate_report(day_folder, report_records)
        print(f"[OK] Daily Excel Report Created: {excel_path}")
    else:
        print("[*] No new downloads today; all addendums are up to date.")

    # Record run in Master Excel Tracker
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
    if stats["filtered_by_date"] > 0:
        print(f"  • Filtered by Cutoff   : {stats['filtered_by_date']} (older than cutoff)")
    print(f"  • Master Excel Tracker : data/addendum_master_tracker.xlsx")
    print(f"  • Day Folder Location  : downloads/{day_folder}/")
    print("=" * 70)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Automated AMC Addendum Downloader")
    parser.add_argument("--amc", type=str, default=None, help="Filter by AMC ID or name")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of AMCs to check")
    parser.add_argument("--from-date", type=str, default=None, help="Cutoff date (e.g. 2026-07-01 or 01-07-2026) to ignore older addenda")
    parser.add_argument("--import-folder", type=str, default=None, help="Folder path of existing PDFs to register into Master Excel Tracker")
    parser.add_argument("--dry-run", action="store_true", help="Preview new addendums without downloading")
    parser.add_argument("--force", action="store_true", help="Force re-download even if already in tracker")
    args = parser.parse_args()

    if args.import_folder:
        import_folder_into_tracker(args.import_folder)
    else:
        run_daily_download(
            amc_filter=args.amc,
            limit=args.limit,
            from_date_str=args.from_date,
            dry_run=args.dry_run,
            force=args.force
        )

