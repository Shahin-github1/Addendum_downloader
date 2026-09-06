# Enterprise System Documentation
## Automated Indian Mutual Fund Statutory Addendum & Notice Acquisition System

---

## 1. Executive Summary & Purpose

In compliance with **Securities and Exchange Board of India (SEBI)** regulations, Asset Management Companies (AMCs) in India are legally obligated to publish **Notices-cum-Addenda** whenever material changes occur to mutual fund schemes or operations. These include:
* Modifications to Scheme Information Documents (SID) and Key Information Memorandums (KIM)
* Changes in Fund Management responsibilities or Key Managerial Personnel (KMP)
* Shifts in Scheme Risk-o-meters and Benchmark Indices
* Revisions to Total Expense Ratios (TER) and Base Expense Ratios (BER)
* Mergers, scheme consolidations, or categorizations
* Declaration of Income Distribution cum Capital Withdrawal (IDCW / Dividends)

### 1.1 Business Objective
The **Automated AMC Addendum Downloader** eliminates the manual effort of visiting 50 distinct AMC websites each morning. The system automatically:
1. Crawls and aggregates all newly released regulatory notices and addenda daily.
2. Downloads genuine, tamper-proof `.pdf` files into day-wise folders.
3. Automatically eliminates routine operational noise (such as fortnightly portfolios or unaudited financials).
4. Generates an organized, hyperlinked **Excel Summary Report** ready for distribution to compliance, research, and operations teams.

---

## 2. Technology Stack & Enterprise Rationale

| Component | Technology | Enterprise Rationale |
| :--- | :--- | :--- |
| **Core Runtime** | Python 3.11 (64-bit) | Highly dependable, cross-platform standard with enterprise-grade networking and data processing libraries. |
| **Networking & HTTP** | `requests` + `urllib3` | Provides HTTP keep-alive session pooling, automatic SSL validation, and sub-second retrieval times without browser overhead. |
| **Document Parser** | `lxml` (C-based `libxml2`) | Industry benchmark for high-speed XML/HTML parsing. Executes XPath queries across large document trees in milliseconds. |
| **Browser Engine** | `Selenium 4` (Chromium/Edge) | Headless browser fallback specifically for JavaScript-heavy Single Page Applications (React/Angular) and anti-bot systems. |
| **Database** | Embedded `SQLite3` | Zero-configuration, ACID-compliant database requiring no external database server or IT maintenance. |
| **Spreadsheet Engine** | `openpyxl` | Generates native Microsoft Excel (`.xlsx`) workbooks complete with styles, formatting, and live `=HYPERLINK` formulas without requiring MS Office installed on the host machine. |
| **Packaging** | `PyInstaller` | Bundles the complete system into a standalone `.exe` so non-technical staff can run it via a single click. |

---

## 3. Statutory AMC Catalog & Data Acquisition Methods

The system monitors **50 Asset Management Companies** in India. Below is the operational mapping of portals and data acquisition methods:

| # | AMC Name | Portal Disclosure URL | Data Acquisition Method |
| :--- | :--- | :--- | :--- |
| 1 | **360 ONE Asset Management** | [Downloads Portal](https://www.360.one/asset/mutual-funds/downloads/) | Headless browser with disclaimer dismissal |
| 2 | **Abakkus Mutual Fund** | [Statutory Disclosures](https://www.abakkusmf.com/statutory-disclosures.html) | Direct HTTP GET / DOM Parser |
| 3 | **Aditya Birla Sun Life MF** | [Addendums Portal](https://mutualfund.adityabirlacapital.com/forms-and-downloads/addendums) | Fast HTTP GET / Categorized Feed |
| 4 | **AlphaGrep Mutual Fund** | [Disclosures](https://www.alphagrepmf.ai/disclosures) | Fast HTTP GET / DOM Parser |
| 5 | **Angel One Mutual Fund** | [Downloads](https://www.angelonemf.com/downloads) | Fast HTTP GET / Document Table |
| 6 | **Axis Mutual Fund** | [Statutory Disclosures](https://www.axismf.com/statutory-disclosures) | Headless Browser with Tab Filter |
| 7 | **Bajaj Finserv Mutual Fund** | [Notice-Addendums](https://www.bajajamc.com/downloads?notice-addendums=) | Fast HTTP GET / Filtered URL |
| 8 | **Bandhan Mutual Fund** | [Addendums](https://bandhanmutual.com/downloads/addendums) | React Client Rendering / DOM Parser |
| 9 | **Baroda BNP Paribas MF** | [Notice-cum-Addenda](https://www.barodabnpparibasmf.in/downloads/notice-cum-addenda) | Fast HTTP GET / Document Listing |
| 10 | **Bank of India Mutual Fund** | [Addenda Notice](https://www.boimf.in/regulatory-reports/addenda-notice) | Fast HTTP GET / DOM Parser |
| 11 | **Canara Robeco Mutual Fund** | [Notice-cum-Addendum](https://www.canararobeco.com/documents/forms-downloads/notice-cum-addendum/) | Dynamic FY URL Query Parameter |
| 12 | **Capitalmind Mutual Fund** | [Statutory Disclosures](https://capitalmindmf.com/statutory-disclosures.html) | Fast HTTP GET / Table Extraction |
| 13 | **Choice Mutual Fund** | [Notices](https://choicemf.com/disclosures/notices) | Fast HTTP GET / Statutory Notices |
| 14 | **DSP Mutual Fund** | [Downloads](https://www.dspim.com/downloads?category=Notices%20and%20Addendum&sub_category=Addendum) | Categorized URL Query Feed |
| 15 | **Edelweiss Mutual Fund** | [Notice-cum-Addendum](https://www.edelweissmf.com/downloads/notice-cum-addendum) | Fast HTTP GET / DOM Parser |
| 16 | **Franklin Templeton MF** | [Fund Documents](https://www.franklintempletonindia.com/downloads/fund-documents) | Fast HTTP GET / Filtered Document Catalog |
| 17 | **Groww Mutual Fund** | [Addendum](https://www.growwmf.in/downloads/addendum) | Fast HTTP GET / Document List |
| 18 | **HDFC Mutual Fund** | [Addenda Notices](https://www.hdfcfund.com/statutory-disclosure/form-disclosures/addenda-notices) | Fast HTTP GET / Regulatory Disclosures |
| 19 | **Helios Mutual Fund** | [Downloads](https://www.heliosmf.in/downloads/) | Fast HTTP GET / Table Extraction |
| 20 | **HSBC Mutual Fund** | [Notice Ads](https://www.assetmanagement.hsbc.co.in/en/mutual-funds/investor-resources?Cap=&Doc=notice-ads) | Categorized Parameter Feed |
| 21 | **ICICI Prudential MF** | [Announcements](https://www.icicipruamc.com/media-center/announcements) | Media Center Regulatory Feed |
| 22 | **Invesco Mutual Fund** | [Literature & Form](https://invescomutualfund.com/literature-and-form?tab=Addendums) | Query Filtered Tab Feed |
| 23 | **ITI Mutual Fund** | [Downloads](https://www.itiamc.com/downloads) | Headless Browser / Catalog Service |
| 24 | **Jio BlackRock AMC** | [Notice-cum-Addendums](https://www.jioblackrockamc.com/statutory-disclosure/addendum-and-notices/notice-cum-addendums) | Dedicated Direct Subpath Route |
| 25 | **JM Financial Mutual Fund** | [Notice-and-Addendums](https://www.jmfinancialmf.com/downloads/Notice-and-Addendums) | Re-routed Document Portal |
| 26 | **Kotak Mahindra MF** | [Forms and Downloads](https://www.kotakmf.com/Information/forms-and-downloads) | Headless Browser with Bot-Bypass |
| 27 | **LIC Mutual Fund** | [Addendum Notice](https://www.licmf.com/addendum-notice) | Fast HTTP GET / Document Table |
| 28 | **Mahindra Manulife MF** | [Downloads](https://www.mahindramanulife.com/downloads) | Disclaimer Dismissal + Document Parser |
| 29 | **Mirae Asset Mutual Fund** | [Addendum](https://www.miraeassetmf.co.in/downloads/statutory-disclosure/addendum) | Fast HTTP GET / Document Table |
| 30 | **Motilal Oswal MF** | [Addendums](https://www.motilaloswalmf.com/downloads/addendums) | Fast HTTP GET / Comprehensive Catalog |
| 31 | **Navi Mutual Fund** | [Addendums](https://navi.com/mutual-fund/downloads/addendums) | Fast HTTP GET / DOM Parser |
| 32 | **Nippon India Mutual Fund** | [Notice Addendum](https://mf.nipponindiaim.com/investor-service/quick-links/notice-addendum) | Fast HTTP GET / High-Volume Archive |
| 33 | **NJ Mutual Fund** | [Downloads](https://downloads.njmutualfund.com/downloads.php) | Fast HTTP GET / Document Handler |
| 34 | **PGIM India Mutual Fund** | [Addenda Notices](https://www.pgimindia.com/mutual-funds/disclosures/Addenda-Notices/Addenda-Notices) | Direct Statutory Disclosure Hub |
| 35 | **PPFAS Mutual Fund** | [Addendum](https://amc.ppfas.com/downloads/addendum/) | Fast HTTP GET / Regulatory Archive |
| 36 | **Quant Mutual Fund** | [Addendum](https://quantmutual.com/downloads/addendum) | Fast HTTP GET / Document List |
| 37 | **Quantum Mutual Fund** | [Regulatory Disclosures](https://www.quantumamc.com/Download-document#headingOne) | Internal Document Handler (`/regulatory-document/`) |
| 38 | **SAMCO Mutual Fund** | [Downloads](https://www.samcomf.com/downloads) | Fast HTTP GET / Table Extraction |
| 39 | **SBI Mutual Fund** | [Notice and Addendums](https://www.sbimf.com/notice-and-addendums) | **Direct REST AJAX Endpoint** (`/ajaxcall/CMS/GetNoticeandAddendumsData`) |
| 40 | **Shriram Mutual Fund** | [Addenda Notice](https://www.shriramamc.in/AmcDwnldAddendaNotice.aspx) | Fast HTTP GET / ASPX Document List |
| 41 | **Sundaram Mutual Fund** | [Addendum Notice](https://www.sundarammutual.com/addendum-notice) | **Direct Static JSON Feeds** (`/Upload/JSON/Addenda/{Year}_Addenda.json`) |
| 42 | **Tata Mutual Fund** | [Notice Addendum](https://www.tatamutualfund.com/notice-addendum/tmf) | Fast HTTP GET / Document Table |
| 43 | **Taurus Mutual Fund** | [Addendum Notices](https://taurusmutualfund.com/addendum-notices) | **Exposed Drupal Filter Feed** (`?field_addendum_notices_year_target_id=All`) |
| 44 | **Trust Mutual Fund** | [Downloads](https://www.trustmf.com/downloads) | **Direct REST API Endpoint** (`/api/api/Trust/GetData`) |
| 45 | **Unifi Capital Mutual Fund**| [Statutory Documents](https://unifimf.com/statutorydocuments/) | Fast HTTP GET / Document List |
| 46 | **Union Mutual Fund** | [Downloads](https://www.unionmf.com/about-us/downloads) | **Direct OData REST API** (`/api/downloads/documents`) |
| 47 | **UTI Mutual Fund** | [Forms & Downloads](https://www.utimf.com/downloads/addenda-financial-year) | Angular SPA Addenda Trigger |
| 48 | **The Wealth Company AMC** | [Addendum and Notices](https://www.wealthcompanyamc.in/literature-forms/statutory-disclosures/addendum-and-notices/) | **Client-Side Event Interceptor** (MUI Action Hooks) |
| 49 | **WhiteOak Capital MF** | [Regulatory Disclosures](https://mf.whiteoakamc.com/regulatory-disclosures) | Fast HTTP GET / Client Hydration |
| 50 | **Zerodha Fund House** | [Addendums and Notices](https://www.zerodhafundhouse.com/resources/addendums-and-notices/) | Fast HTTP GET / Clean Title Normalization |

---

## 4. Operating Standard Operating Procedure (SOP)

### 4.1 Daily Execution
Every business morning, designated operational personnel run the tool via either:
* **Option A (One-Click Launcher)**: Double-click `run_daily_downloader.bat` on the Desktop.
* **Option B (Automated Windows Task)**: Configured in Windows Task Scheduler to execute automatically at 08:00 AM.
* **Option C (Command Line)**:
  ```powershell
  python main.py
  ```

### 4.2 Output Folder Hierarchy
All outputs are created under the `downloads/` directory, segmented strictly by current calendar date:
```
downloads/
└── 7th September 2026/
    ├── Addendum_Summary_7th_September_2026.xlsx
    ├── [SBI Mutual Fund] - notice-cum-addendum-for-merger-of-schemes.pdf
    ├── [The Wealth Company AMC] - Addendum 24 (2026-27) Hybrid Schemes-Categorisation.pdf
    ├── [Sundaram Mutual Fund] - Notice cum Addendum for Change in Categorisation.pdf
    ├── [Trust Mutual Fund] - 58_2026 - Change in Riskometer of TRUSTMF Short Term Fund.pdf
    ├── [Union Mutual Fund] - Amendment to SAI.pdf
    └── [Franklin Templeton Mutual Fund] - Addendum-Addition-of-2-CAMS-Location.pdf
```

### 4.3 Summary Excel Report Format
The auto-generated Excel report (`Addendum_Summary_<Date>.xlsx`) includes the following columns:

| Column | Header | Description | Example |
| :---: | :--- | :--- | :--- |
| **A** | AMC Name | Official AMC Name | `SBI Mutual Fund` |
| **B** | Document Title | Exact regulatory title of the filing | `Notice cum Addendum for Merger of Schemes` |
| **C** | Date | Publication date detected in document/source | `04-Sep-2026` |
| **D** | PDF URL | Live clickable hyperlink to official online notice | `[Open Notice](https://www.sbimf.com/...)` |
| **E** | Local Filename | Actual sanitized filename stored on disk | `[SBI Mutual Fund] - notice-cum-addendum...pdf` |
| **F** | File Size (KB) | Actual file size on disk | `245.8 KB` |
| **G** | Downloaded At | Accurate audit timestamp (YYYY-MM-DD HH:MM:SS) | `2026-09-07 08:14:22` |

---

## 5. Compliance, Security & Data Integrity Controls

1. **Tamper-Proof File Guarantee**:
   The engine enforces magic-byte inspection (`%PDF-`). Any server error, login wall, or captive portal returning HTML is instantly rejected. Corrupted files can never enter the compliance folder.
2. **Audit Trail & Immutability**:
   Every downloaded document is timestamped and recorded in an immutable SQLite database (`data/addendum_tracker.db`) with its MD5 hash and origin URL.
3. **Bandwidth & Rate Compliance**:
   The engine uses gentle request pacing and connection keep-alive to ensure compliance with web security guidelines and prevent rate-limiting or server degradation on AMC portals.
