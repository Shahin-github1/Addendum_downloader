import os
import re
import hashlib
import time
import urllib.parse
from typing import Optional, Dict, Any
import requests
import urllib3

# Suppress SSL verification warnings for AMCs with self-signed certificate chains
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .date_utils import clean_filename, get_app_root

class PDFDownloader:
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    def __init__(self, base_download_dir: str = None):
        if base_download_dir is None:
            base_dir = get_app_root()
            base_download_dir = os.path.join(base_dir, "downloads")
        self.base_download_dir = base_download_dir
        os.makedirs(self.base_download_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    @staticmethod
    def sanitize_url(raw_url: str) -> str:
        """Properly URL-encodes spaces and special characters in URL path."""
        parts = list(urllib.parse.urlsplit(raw_url.strip()))
        # Quote path while keeping existing slashes
        parts[2] = urllib.parse.quote(urllib.parse.unquote(parts[2]), safe="/@:")
        # Quote query if needed
        return urllib.parse.urlunsplit(parts)

    @staticmethod
    def extract_original_filename(
        pdf_url: str,
        resp_headers: Optional[Dict[str, str]] = None,
        fallback_title: Optional[str] = None
    ) -> str:
        """
        Preserves the exact original filename from HTTP headers or the URL path.
        Does NOT rename or standardize, only sanitizes characters prohibited by Windows filesystem.
        """
        raw_name = ""

        # 1. Check Content-Disposition header if available
        if resp_headers:
            cd = resp_headers.get('Content-Disposition') or resp_headers.get('content-disposition') or ""
            if cd:
                m_star = re.search(r"filename\*\s*=\s*UTF-8''([^;]+)", cd, re.I)
                if m_star:
                    raw_name = urllib.parse.unquote(m_star.group(1).strip())
                else:
                    m = re.search(r'filename\s*=\s*"?([^";]+)"?', cd, re.I)
                    if m:
                        raw_name = m.group(1).strip()

        # 2. Extract from URL path
        if not raw_name:
            unquoted_url = urllib.parse.unquote(pdf_url.strip())
            parsed = urllib.parse.urlsplit(unquoted_url)
            path_part = parsed.path.rstrip('/')
            base = os.path.basename(path_part)
            if base:
                if base.lower().endswith('.pdf'):
                    raw_name = base
                else:
                    # Check query string for embedded file parameters
                    qs = urllib.parse.parse_qs(parsed.query)
                    for qk in ['file', 'name', 'doc', 'filename', 'document', 'download']:
                        if qk in qs and qs[qk][0]:
                            cand = os.path.basename(qs[qk][0])
                            if cand.lower().endswith('.pdf'):
                                raw_name = cand
                                break
                    if not raw_name:
                        raw_name = base

        # 3. Fallback to title if still empty
        if not raw_name:
            raw_name = fallback_title or "Addendum.pdf"

        # Sanitize only illegal Windows filesystem characters: \ / : * ? " < > |
        raw_name = re.sub(r'[\x00-\x1f\\/*?:"<>|]', '_', raw_name)
        raw_name = raw_name.strip(' .')  # Remove illegal leading/trailing dots or spaces

        if not raw_name.lower().endswith('.pdf'):
            raw_name = f"{raw_name}.pdf"

        return raw_name[:180]

    def download_file(
        self,
        pdf_url: str,
        amc_name: str,
        doc_title: str,
        day_folder_name: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Downloads a PDF preserving the original AMC filename, organized by AMC subfolder:
        downloads/{day_folder_name}/{sanitized_amc}/{original_filename}.pdf
        """
        sanitized_amc = clean_filename(amc_name)
        target_dir = os.path.join(self.base_download_dir, day_folder_name, sanitized_amc)
        os.makedirs(target_dir, exist_ok=True)

        clean_url = self.sanitize_url(pdf_url)
        headers = {'Referer': clean_url}

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(clean_url, headers=headers, verify=False, timeout=18)
                if resp.status_code != 200:
                    raise ValueError(f"HTTP {resp.status_code}")

                content = resp.content
                if not content or len(content) < 400:
                    raise ValueError(f"File too small ({len(content)} bytes), likely an error response.")

                # Enforce strict PDF signature (magic bytes: %PDF-)
                if b"%PDF-" not in content[:1024]:
                    snippet = content[:60].decode('utf-8', errors='ignore').replace('\n', ' ')
                    raise ValueError(f"Server returned non-PDF content (starts with: '{snippet}')")

                # Extract exact original filename from headers or URL
                orig_fname = self.extract_original_filename(clean_url, resp.headers, doc_title)
                dest_path = os.path.join(target_dir, orig_fname)

                # Avoid intra-folder collisions if identical filename already exists
                counter = 1
                name_root, name_ext = os.path.splitext(orig_fname)
                while os.path.exists(dest_path):
                    dest_path = os.path.join(target_dir, f"{name_root}_{counter}{name_ext}")
                    counter += 1

                # Calculate MD5 hash
                file_hash = hashlib.md5(content).hexdigest()

                # Write to disk
                with open(dest_path, "wb") as f:
                    f.write(content)

                file_size_kb = round(len(content) / 1024.0, 2)
                return {
                    "success": True,
                    "file_path": dest_path,
                    "file_name": os.path.basename(dest_path),
                    "file_size_kb": file_size_kb,
                    "file_hash": file_hash,
                    "error": None
                }

            except Exception as e:
                last_error = str(e)
                time.sleep(1.0 * attempt)

        return {
            "success": False,
            "file_path": None,
            "file_name": None,
            "file_size_kb": 0.0,
            "file_hash": None,
            "error": last_error
        }

