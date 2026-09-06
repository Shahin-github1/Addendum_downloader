# Automated Indian AMC Addendum Downloader

A dependable, production-grade automation system designed to download and track daily Addendums, Notices, and Statutory Disclosures across **50 Indian Asset Management Companies (AMCs)**.

---

## 📚 Complete System Documentation

For detailed technical architectures and enterprise operational guides, please refer to:
* 🛠️ **[Developer & Technical Manual](file:///c:/Users/Shahin%20Chakraborty/Desktop/adendum_download/DEVELOPER_MANUAL.md)**: Full codebase explanation, architectural rationale, code walkthrough, and new machine setup guide.
* 🏢 **[Office & Enterprise System Documentation](file:///c:/Users/Shahin%20Chakraborty/Desktop/adendum_download/OFFICE_SYSTEM_DOCUMENTATION.md)**: Comprehensive business documentation, technology justifications, statutory disclosure catalogs across all 50 AMCs, and standard operating procedures (SOP).

---

## 🌟 Key Features

1. **Dependable & Incremental (Never Misses & No Duplicates)**:
   * Uses an **SQLite database** (`data/addendum_tracker.db`) to record every downloaded document's URL, publication date, and MD5 file hash.
   * On daily runs, only **new** addendums are downloaded; existing files are verified and skipped in seconds.
2. **Day-Wise Folder Organization**:
   * Saves files into clean date-named folders, e.g.:
     ```
     downloads/
     └── 6th September 2026/
         ├── Addendum_Summary_6th_September_2026.xlsx
         ├── [Groww Mutual Fund] - 24. Notice - Change in BER.pdf
         ├── [DSP Mutual Fund] - 47.-notice-cum-addendum-to-sid-kim-change-in-fund-manager-s.pdf
         └── [Zerodha Fund House] - Addendum No. 15 - 2026-27.pdf
     ```
3. **Automated Excel Report Generation**:
   * Automatically generates an Excel report (`Addendum_Summary_<Date>.xlsx`) in each day's folder with:
     * AMC Name
     * Document Title
     * Publication Date
     * Clickable Hyperlink to the original source URL
     * Downloaded File Name
     * File Size in KB
     * Timestamp
4. **Resilient Multi-Tier Extraction**:
   * **Tier 1 (Fast HTTP)**: Handles ~75% of AMCs in sub-seconds via `requests` session pooling.
   * **Tier 2 (Headless Edge/Chrome)**: Automatically handles JavaScript SPAs (React/Angular), dynamic tabs, and accordions without relying on brittle CSS class selectors.
5. **Dynamic Indian Financial Year Engine**:
   * Automatically computes the active Financial Year (`2026-27`, `2027-28`, etc.) based on today's date so year-based dropdowns and query parameters never expire.
6. **Executable Ready (`.exe`)**:
   * Can be run with Python or double-clicked as a standalone Windows executable.

---

## 🚀 How to Run

### Option 1: One-Click Runner (Easiest)
Simply double-click:
```text
run_daily_downloader.bat
```

### Option 2: Command Line (Python)
Run all 50 AMCs:
```bash
python main.py
```

Run for a specific AMC:
```bash
python main.py --amc zerodha
python main.py --amc groww
python main.py --amc dsp
```

Preview without downloading (Dry Run):
```bash
python main.py --dry-run
```

### Option 3: Standalone Windows Executable (.exe)
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
