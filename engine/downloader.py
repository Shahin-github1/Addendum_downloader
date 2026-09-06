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

    def download_file(
        self,
        pdf_url: str,
        amc_name: str,
        doc_title: str,
        day_folder_name: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Downloads a PDF and saves it into:
        downloads/{day_folder_name}/[{amc_name}] - {doc_title}.pdf
        """
        target_dir = os.path.join(self.base_download_dir, day_folder_name)
        os.makedirs(target_dir, exist_ok=True)

        # Generate clean filename
        sanitized_amc = clean_filename(amc_name)
        sanitized_title = clean_filename(doc_title)
        if not sanitized_title.lower().endswith(".pdf"):
            base_fname = f"[{sanitized_amc}] - {sanitized_title}.pdf"
        else:
            base_fname = f"[{sanitized_amc}] - {sanitized_title}"

        dest_path = os.path.join(target_dir, base_fname)
        counter = 1
        name_root, name_ext = os.path.splitext(base_fname)
        while os.path.exists(dest_path):
            dest_path = os.path.join(target_dir, f"{name_root}_{counter}{name_ext}")
            counter += 1

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
