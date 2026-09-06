# Automated Indian AMC Addendum Downloader

A dependable, production-grade automation system designed to download and track daily Addendums, Notices, and Statutory Disclosures across **50 Indian Asset Management Companies (AMCs)**.

---

## 📚 Complete System Documentation

For detailed technical architectures and enterprise operational guides, please refer to:
* 🛠️ **[Developer & Technical Manual](file:///c:/Users/Shahin%20Chakraborty/Desktop/adendum_download/DEVELOPER_MANUAL.md)**: Full codebase explanation, architectural rationale, code walkthrough, and new machine setup guide.
* 🏢 **[Office & Enterprise System Documentation](file:///c:/Users/Shahin%20Chakraborty/Desktop/adendum_download/OFFICE_SYSTEM_DOCUMENTATION.md)**: Comprehensive business documentation, technology justifications, statutory disclosure catalogs across all 50 AMCs, and standard operating procedures (SOP).

---

## 🌟 Key Features

1. **Excel Master Tracker (`data/addendum_master_tracker.xlsx`)**:
   * Replaces complex databases with a clean, visual Microsoft Excel master ledger.
   * Tracks every downloaded document across all AMCs with publication dates, file sizes, MD5 hashes, and direct clickable links to open the local PDF.
   * Zero IT setup or database permissions required; fully transparent and shareable.
2. **Preserves 100% Original Server File Names**:
   * Keeps the exact initial file name from the AMC's server (e.g. `Notice_15072026.pdf`, `2026_Notice_Ad_07.pdf`) rather than arbitrary renaming.
   * Organized into clean per-AMC subfolders to eliminate any name collisions across AMCs:
     ```
     downloads/
     └── 10th September 2026/
         ├── Addendum_Summary_10th_September_2026.xlsx
         ├── SBI Mutual Fund/
         │   └── Notice_15072026.pdf
         ├── Sundaram Mutual Fund/
         │   └── 2026_Notice_Ad_07.pdf
         └── Motilal Oswal Mutual Fund/
             └── Notice_cum_addendum_12.pdf
     ```
3. **Configurable Date Range Filtering (`--from-date`)**:
   * Set a cutoff date (e.g. `--from-date 2026-07-01`) so the system only downloads addenda published on or after that date, skipping older historical files.
4. **Historical Archive Importer (`import_existing.py`)**:
   * Easily ingest months of previously downloaded files from any folder into the Excel tracker so the downloader recognizes them and never downloads duplicates.
5. **Automated Daily Excel Summary Report**:
   * Generates a standalone Excel summary report (`Addendum_Summary_<Date>.xlsx`) in each day's folder with formatted tables and clickable URLs.
6. **Resilient Multi-Tier Extraction**:
   * **Direct APIs & CMS AJAX**: Ultra-fast endpoints for high-volume AMCs (SBI, Sundaram, Trust, Union).
   * **Tier 1 (Fast HTTP)**: Handles ~75% of AMCs in sub-seconds via `requests` session pooling.
   * **Tier 2 (Headless Browser)**: Automated fallback for dynamic JavaScript SPAs (React/Angular).
7. **Dynamic Indian Financial Year Engine**:
   * Automatically computes the active Financial Year (`2026-27`, `2027-28`, etc.) based on today's date so year-based queries never expire.

---

## 🚀 How to Run

### Option 1: One-Click Runner (Easiest)
Simply double-click:
```text
run_daily_downloader.bat
```

### Option 2: Command Line (Python)
Run all AMCs (Normal Live Mode):
```bash
python main.py
```

Run with Date Filter (e.g. July 1st, 2026 onwards):
```bash
python main.py --from-date 2026-07-01
```

Run for a specific AMC:
```bash
python main.py --amc sbi
python main.py --amc sundaram
python main.py --amc "motilal oswal"
```

Preview without downloading (Dry Run):
```bash
python main.py --dry-run --limit 5
```

### Option 3: Ingest Existing Past Downloads (One-Time Setup)
If you already have a folder of previously downloaded addenda and want to register them into the Excel tracker to prevent re-downloading:
```bash
python import_existing.py --folder "C:\path\to\your\previous_downloads"
```

### Option 4: Standalone Windows Executable (.exe)
Located in:
```text
dist\AMC_Addendum_Downloader\AMC_Addendum_Downloader.exe
```
To rebuild the executable at any time, run:
```bash
build_exe.bat
```

---

## ⏰ How to Schedule Daily Execution in Windows (Task Scheduler)

You can set this to run automatically every morning at, say, 8:00 AM:

1. Press `Win + R`, type `taskschd.msc`, and press **Enter**.
2. Click **Create Basic Task...** in the right-hand panel.
3. **Name**: `Daily AMC Addendum Downloader`.
4. **Trigger**: Select **Daily** and set your desired time (e.g. `08:00 AM`).
5. **Action**: Select **Start a program**.
6. **Program/script**: Click Browse and select:
   `c:\Users\Shahin Chakraborty\Desktop\adendum_download\run_daily_downloader.bat`
7. **Start in (optional)**: Enter the folder path:
   `c:\Users\Shahin Chakraborty\Desktop\adendum_download`
8. Click **Finish**.

---

## ⚙️ Adding or Customizing AMCs

All 50 AMCs are declared in:
```text
config/amc_catalog.json
```
Each AMC configuration includes:
* `id`: Unique identifier (e.g. `zerodha`, `hdfc`, `canara_robeco`)
* `name`: Display name
* `url`: Target web page
* `enabled`: `true` / `false`
