import os
import re
import json
import time
import datetime
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
import urllib3
from lxml import html

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Selenium for Tier-2 dynamic client-side rendering
try:
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from .date_utils import get_indian_financial_year, clean_filename

class AMCExtractor:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    DATE_PATTERNS = [
        re.compile(r'\b(\d{1,2}[-/.](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/.]\d{2,4})\b', re.I),
        re.compile(r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b', re.I),
        re.compile(r'\b(\d{1,2}[-/. ]\d{1,2}[-/. ]\d{2,4})\b'),
        re.compile(r'\b(\d{4}[-/. ]\d{1,2}[-/. ]\d{1,2})\b'),
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._driver = None

    def _get_driver(self):
        if not SELENIUM_AVAILABLE:
            return None
        if self._driver is None:
            options = EdgeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")
            options.add_argument(f"user-agent={self.HEADERS['User-Agent']}")
            try:
                self._driver = webdriver.Edge(options=options)
            except Exception:
                try:
                    from selenium.webdriver.chrome.options import Options as ChromeOptions
                    c_opts = ChromeOptions()
                    c_opts.add_argument("--headless=new")
                    c_opts.add_argument("--window-size=1920,1080")
                    c_opts.add_argument("--disable-gpu")
                    c_opts.add_argument("--no-sandbox")
                    c_opts.add_argument(f"user-agent={self.HEADERS['User-Agent']}")
                    self._driver = webdriver.Chrome(options=c_opts)
                except Exception:
                    self._driver = None
            if self._driver:
                self._driver.set_page_load_timeout(15)
                self._driver.set_script_timeout(10)
        return self._driver

    def close(self):
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    def extract_addendums(self, amc: Dict[str, Any], from_date: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """
        Main extraction entry point for an AMC.
        Tier 1: Fast HTTP GET/POST with requests.
        Tier 2: Headless Browser Fallback for SPAs.
        """
        raw_url = amc.get("url", "")
        fy_info = get_indian_financial_year()
        url = raw_url.replace("{current_fy}", fy_info["short"])
        url = url.replace("{current_year}", fy_info["start_year"])

        amc_name = amc.get("name", "AMC")
        amc_id = amc.get("id", "amc")

        # Direct API Handlers
        if amc_id == "sbi":
            items = self._extract_sbi(amc_id, amc_name, from_date=from_date)
            if items and len(items) > 0:
                return items

        if amc_id == "sundaram":
            items = self._extract_sundaram(amc_id, amc_name)
            if items and len(items) > 0:
                return items

        if amc_id == "trust":
            items = self._extract_trust(amc_id, amc_name)
            if items and len(items) > 0:
                return items

        if amc_id == "union":
            items = self._extract_union(amc_id, amc_name)
            if items and len(items) > 0:
                return items

        # Tier 1: Fast HTTP GET
        items = self._extract_via_http(url, amc_id, amc_name)
        if items and len(items) > 0:
            return items

        # Tier 2: Dynamic Headless Browser Fallback
        items = self._extract_via_browser(url, amc_id, amc_name)
        return items

    def _extract_sbi(self, amc_id: str, amc_name: str, from_date: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        api_url = 'https://www.sbimf.com/ajaxcall/CMS/GetNoticeandAddendumsData'
        headers = {
            'User-Agent': self.HEADERS['User-Agent'],
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.sbimf.com/notice-and-addendums',
        }
        from_str = from_date.strftime("%d/%m/%Y") if from_date else "01/01/2025"
        payload = {'AddendumType': 'Scheme Information', 'FromDate': from_str, 'ToDate': '09/07/2026'}
        try:
            r = requests.post(api_url, headers=headers, json=payload, verify=False, timeout=15)
            if r.status_code == 200 and r.text:
                return self._parse_html_for_addendums(r.text, 'https://www.sbimf.com', amc_id, amc_name)
        except Exception:
            pass
        return []


    def _extract_sundaram(self, amc_id: str, amc_name: str) -> List[Dict[str, Any]]:
        extracted = []
        seen = set()
        for yr in ['2026', '2025']:
            for cat in ['Addenda', 'NoticeAd']:
                url = f"https://www.sundarammutual.com/Upload/JSON/Addenda/{yr}_{cat}.json"
                try:
                    r = self.session.get(url, verify=False, timeout=10)
                    if r.status_code == 200:
                        for item in r.json().get('FAY', []):
                            fp = item.get('FP', '').strip()
                            dn = item.get('DN', '').strip()
                            if not fp:
                                continue
                            full_url = urllib.parse.urljoin('https://www.sundarammutual.com', fp)
                            if full_url in seen:
                                continue
                            if any(np in dn.lower() for np in ['fortnightly portfolio', 'monthly portfolio', 'half yearly portfolio', 'annual report']):
                                continue
                            extracted.append({
                                "amc_id": amc_id,
                                "amc_name": amc_name,
                                "doc_title": dn,
                                "doc_date": self._find_date(f"{dn} {fp}"),
                                "pdf_url": full_url
                            })
                            seen.add(full_url)
                except Exception:
                    pass
        return extracted

    def _extract_trust(self, amc_id: str, amc_name: str) -> List[Dict[str, Any]]:
        url = 'https://www.trustmf.com/api/api/Trust/GetData'
        headers = {
            'User-Agent': self.HEADERS['User-Agent'],
            'Content-Type': 'application/json; charset=UTF-8',
        }
        payload = {
            'systemQueryFileName': 'downloadablesweb.xml',
            'tagName': 'GetDownloadableByType',
            'searchField': '',
            'searchValue': '',
            'sortField': 'uploaddate',
            'sortDirection': 'DESC',
            'replaceField': '_slug_',
            'replaceValue': 'addendum'
        }
        extracted = []
        try:
            r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
            if r.status_code == 200:
                data = r.json()
                items = data.get('resultSetArray', [])
                for it in items:
                    title = it.get('title', '').strip()
                    fileurl = it.get('fileurl', '').strip()
                    uploaddate = it.get('uploaddate', '').strip()
                    if fileurl and '.pdf' in fileurl.lower():
                        clean_title = re.sub(r'[\r\n\t]+', ' ', title).strip()
                        clean_title = clean_title.encode('ascii', errors='ignore').decode('ascii').strip()
                        extracted.append({
                            "amc_id": amc_id,
                            "amc_name": amc_name,
                            "doc_title": clean_title or "Notice cum Addendum",
                            "doc_date": self._find_date(f"{uploaddate} {clean_title}"),
                            "pdf_url": fileurl
                        })
        except Exception:
            pass
        return extracted

    def _extract_union(self, amc_id: str, amc_name: str) -> List[Dict[str, Any]]:
        url = 'https://www.unionmf.com/api/downloads/documents'
        headers = {
            'User-Agent': self.HEADERS['User-Agent'],
            'Referer': 'https://www.unionmf.com/about-us/downloads',
        }
        extracted = []
        seen = set()
        try:
            r = self.session.get(url, headers=headers, verify=False, timeout=15)
            if r.status_code == 200:
                for doc in r.json().get('value', []):
                    t = doc.get('Title', '').strip()
                    u = doc.get('Url', '').strip()
                    if not u or not t:
                        continue
                    full_url = urllib.parse.urljoin('https://www.unionmf.com', u)
                    if full_url in seen:
                        continue
                    if any(k in (t + u).lower() for k in ['addend', 'notice', 'amendment to sai', 'corrigendum']):
                        if any(np in t.lower() for np in ['portfolio', 'financial', 'voting policy', 'factsheet']):
                            continue
                        clean_title = re.sub(r'[\r\n\t]+', ' ', t).strip()
                        clean_title = clean_title.encode('ascii', errors='ignore').decode('ascii').strip()
                        extracted.append({
                            "amc_id": amc_id,
                            "amc_name": amc_name,
                            "doc_title": clean_title or "Notice cum Addendum",
                            "doc_date": self._find_date(f"{clean_title} {u}"),
                            "pdf_url": full_url
                        })
                        seen.add(full_url)
        except Exception:
            pass
        return extracted

    def _extract_via_http(self, url: str, amc_id: str, amc_name: str) -> List[Dict[str, Any]]:
        try:
            resp = self.session.get(url, verify=False, timeout=15)
            if resp.status_code == 200:
                return self._parse_html_for_addendums(resp.text, url, amc_id, amc_name)
            return []
        except Exception:
            return []

    def _extract_via_browser(self, url: str, amc_id: str, amc_name: str) -> List[Dict[str, Any]]:
        driver = self._get_driver()
        if not driver:
            return []
        try:
            try:
                driver.get(url)
            except Exception:
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
            time.sleep(3.5)

            # Wealth Company: Intercept button download actions
            if amc_id == "wealth_company":
                try:
                    driver.execute_script("""
                    window.__opened_urls = [];
                    window.open = function(url) {
                        window.__opened_urls.push(url);
                        return null;
                    };
                    const origClick = HTMLAnchorElement.prototype.click;
                    HTMLAnchorElement.prototype.click = function() {
                        window.__opened_urls.push(this.href);
                        return origClick.apply(this, arguments);
                    };
                    """)
                    btns = driver.find_elements(By.TAG_NAME, 'button')
                    for b in btns:
                        txt = b.text.strip()
                        if 'addendum' in txt.lower() or 'notice' in txt.lower():
                            driver.execute_script("arguments[0].click();", b)
                            time.sleep(0.08)
                    opened = driver.execute_script("return window.__opened_urls || [];")
                    extracted = []
                    idx = 0
                    for b in btns:
                        txt = b.text.strip()
                        clean_title = txt.replace('Download', '').strip()
                        if ('addendum' in clean_title.lower() or 'notice' in clean_title.lower()) and idx < len(opened):
                            u = opened[idx]
                            idx += 1
                            if '.pdf' in u.lower():
                                extracted.append({
                                    "amc_id": amc_id,
                                    "amc_name": amc_name,
                                    "doc_title": clean_title,
                                    "doc_date": self._find_date(f"{clean_title} {u}"),
                                    "pdf_url": u
                                })
                    if extracted:
                        return extracted
                except Exception:
                    pass

            # Sundaram: Select Addenda in dropdown
            if amc_id == "sundaram":
                try:
                    from selenium.webdriver.support.ui import Select
                    s_el = driver.find_element(By.ID, "Sl_Addenda")
                    Select(s_el).select_by_visible_text("Addenda")
                    time.sleep(3)
                except Exception:
                    pass

            page_source = driver.page_source
            return self._parse_html_for_addendums(page_source, url, amc_id, amc_name)
        except Exception:
            return []

    def _parse_html_for_addendums(self, html_content: str, base_url: str, amc_id: str, amc_name: str) -> List[Dict[str, Any]]:
        if not html_content:
            return []

        doc = html.fromstring(html_content)
        extracted = []
        seen_urls = set()

        for a in doc.xpath('//a[@href]'):
            href = a.get('href', '').strip()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue

            full_url = urllib.parse.urljoin(base_url, href)
            if full_url in seen_urls:
                continue

            link_text = " ".join(a.xpath('.//text()')).strip()
            title_attr = a.get('title', '').strip()
            parent_text = " ".join(a.xpath('parent::*//text()')).strip()
            ancestor_row = a.xpath('ancestor::tr | ancestor::li')
            row_text = " ".join(ancestor_row[0].xpath('.//text()')).strip() if ancestor_row else ""

            # Must be a document link (PDF or download handler), not an HTML page/route
            href_clean = href.split('?')[0].lower()
            if href_clean.endswith('/') or any(href_clean.endswith(ext) for ext in ['.html', '.htm', '.aspx', '.php', '.jsp']):
                # Only permit if query string has explicit pdf/file parameter
                if not any(k in href.lower() for k in ['.pdf', 'file=', 'filename=', 'attachment=']):
                    continue

            is_pdf = (
                ('.pdf' in href.lower()) 
                or ('.ashx' in href.lower()) 
                or ('/regulatory-document/addendum-and-news/' in href.lower())
                or ('/docs/default-source/' in href.lower())
                or any(k in href.lower() for k in ['file=', 'filename=', 'attachment='])
            )
            if not is_pdf:
                continue

            # Unquote and normalize URL and context for robust pattern matching
            unquoted_href = urllib.parse.unquote(href)
            normalized_href = re.sub(r'[-_+%20]+', ' ', unquoted_href).lower()
            link_context = f"{normalized_href} {link_text} {title_attr}".lower()
            combined_context = f"{link_context} {parent_text} {row_text}".lower()

            # 1. HARD NOISE FILTER (Scoped strictly to the document and its immediate text)
            noise_patterns = [
                'monthly portfolio', 'fortnightly portfolio', 'half yearly portfolio',
                'portfolio disclosure', 'portfolio statement', 'annual report',
                'half yearly financial', 'unaudited financial', 'stewardship',
                'voting policy', 'proxy voting', 'valuation policy', 'whistle blower',
                'grievance redressal', 'investor protection policy', 'code of conduct',
                'factsheet', 'common application', 'kyc form', 'mandate form',
                'scheme dashboard', 'fund spectrum', 'definition of sid',
                'demat to re-mat', 'tax reckoner'
            ]
            if any(np in link_context for np in noise_patterns):
                continue

            # 2. Base SID/KIM/SAI without addendum is also noise
            if any(k in normalized_href for k in ['_sid.pdf', '_kim.pdf', '_sai.pdf', 'sid final', 'caf form', '/sid/', '/kim/']) and 'addend' not in link_context:
                continue

            # 3. STRICT ADDENDUM FILTER: Must explicitly be an Addendum, Corrigendum, or Regulatory Notice
            is_addendum = (
                any(k in href.lower() for k in ['/addend', 'addenda', '/notice-cum-addenda'])
                or any(k in link_context for k in ['addend', 'corrigendum', 'amendment', 'notice-cum-addend', 'notice cum addend'])
                or (
                    'notice' in link_context and any(k in link_context for k in [
                        'change in', 'merger', 'benchmark', 'riskometer', 'risk-o-meter',
                        'exit load', 'fund manager', 'expense ratio', 'ter', 'ber',
                        'preponement', 'postponement', 'dividend', 'idcw', 'record date', 'opat'
                    ])
                )
            )

            if is_addendum:
                doc_title = self._determine_title(link_text, title_attr, row_text, href)
                doc_date = self._find_date(f"{row_text} {parent_text} {href}")

                extracted.append({
                    "amc_id": amc_id,
                    "amc_name": amc_name,
                    "doc_title": doc_title,
                    "doc_date": doc_date,
                    "pdf_url": full_url
                })
                seen_urls.add(full_url)

        return extracted

    def _determine_title(self, link_text: str, title_attr: str, row_text: str, href: str) -> str:
        # Extract filename from URL
        fname = href.split('?')[0].split('/')[-1]
        fname = urllib.parse.unquote(fname)
        fname_clean = re.sub(r'\.pdf$', '', fname, flags=re.I).strip()

        # If filename itself contains 'addend', 'notice', 'corrigendum', or 'circular'
        if any(k in fname_clean.lower() for k in ['addend', 'notice', 'corrigendum', 'circular']):
            return re.sub(r'\s+', ' ', fname_clean).strip()

        # If link text is descriptive and not generic
        generic_words = {'download', 'click here', 'view', 'read', 'pdf', 'link', 'more'}
        if link_text and link_text.strip().lower() not in generic_words and 4 < len(link_text) < 110:
            if any(k in link_text.lower() for k in ['addend', 'notice', 'scheme', 'fund']):
                return re.sub(r'\s+', ' ', link_text).strip()

        if title_attr and 5 < len(title_attr) < 120:
            return re.sub(r'\s+', ' ', title_attr).strip()

        if row_text:
            lines = [l.strip() for l in row_text.split('\n') if 8 < len(l.strip()) < 120]
            for l in lines:
                if l.lower() not in generic_words and not re.match(r'^\d{1,2}[-/. ]', l):
                    if any(k in l.lower() for k in ['addend', 'notice', 'scheme']):
                        return l.strip()

        return fname_clean or "Notice cum Addendum"

    def _find_date(self, text: str) -> str:
        for pattern in self.DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return time.strftime("%d-%b-%Y")
