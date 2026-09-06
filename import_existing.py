"""
Historical PDF Addendum Importer
Scans an existing folder containing previously downloaded PDF files,
computes their SHA-256/MD5 hashes, and registers them into the
Excel Master Tracker (data/addendum_master_tracker.xlsx).
Once registered, the daily downloader will automatically skip these files.
"""

import os
import sys
import argparse
from engine.excel_tracker import ExcelTracker

def import_folder(folder_path: str):
    if not os.path.exists(folder_path):
        print(f"[!] Target folder does not exist: {folder_path}")
        sys.exit(1)

    print("=" * 75)
    print("      AMC Historical Addendum Ingestion -> Excel Master Tracker")
    print("=" * 75)
    print(f"[*] Target Directory: {folder_path}")

    tracker = ExcelTracker()
    registered = 0
    skipped = 0

    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))

    total = len(pdf_files)
    print(f"[*] Found {total} PDF files. Starting registration...\n")

    for idx, p in enumerate(pdf_files, start=1):
        filename = os.path.basename(p)
        # Attempt to determine AMC name from parent subfolder
        parent_dir = os.path.basename(os.path.dirname(p))
        if parent_dir and parent_dir.lower() not in ["downloads", ".", "pdf", "pdfs", "addenda", "addendum"]:
            amc_name = parent_dir
        else:
            amc_name = "Historical AMC"

        success = tracker.import_local_file(
            file_path=p,
            amc_name=amc_name,
            doc_title=os.path.splitext(filename)[0]
        )

        if success:
            registered += 1
            print(f"[{idx}/{total}] + [REGISTERED] {filename} ({amc_name})")
        else:
            skipped += 1

    print("\n" + "-" * 75)
    print(f"INGESTION SUMMARY:")
    print(f"  • Total PDFs Scanned       : {total}")
    print(f"  • Newly Registered in Excel: {registered}")
    print(f"  • Skipped (Already Tracked): {skipped}")
    print(f"  • Master Tracker Location  : {tracker.tracker_path}")
    print("=" * 75)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Import existing addendum PDFs into Excel Master Tracker")
    parser.add_argument("--folder", type=str, required=True, help="Path to directory containing previously downloaded PDFs")
    args = parser.parse_args()

    import_folder(args.folder)
