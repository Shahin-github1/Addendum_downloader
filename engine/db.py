import sqlite3
import os
from typing import Optional, List, Dict, Any
from .date_utils import get_app_root

class StateTracker:
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = get_app_root()
            db_path = os.path.join(base_dir, "data", "addendum_tracker.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloaded_addendums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amc_id TEXT NOT NULL,
                amc_name TEXT NOT NULL,
                doc_title TEXT,
                doc_date TEXT,
                pdf_url TEXT UNIQUE NOT NULL,
                file_hash TEXT,
                download_date TEXT NOT NULL,
                local_filename TEXT,
                local_path TEXT,
                file_size_kb REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pdf_url ON downloaded_addendums(pdf_url);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_download_date ON downloaded_addendums(download_date);
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS run_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                total_amcs INTEGER,
                new_downloads_count INTEGER,
                skipped_count INTEGER,
                errors_count INTEGER,
                summary_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()

    def is_downloaded(self, pdf_url: str) -> bool:
        """Checks if a PDF has already been downloaded based on URL."""
        if not pdf_url:
            return False
        clean_url = pdf_url.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM downloaded_addendums WHERE pdf_url = ? LIMIT 1;", (clean_url,))
            return cursor.fetchone() is not None

    def record_download(
        self,
        amc_id: str,
        amc_name: str,
        doc_title: str,
        doc_date: str,
        pdf_url: str,
        file_hash: str,
        local_filename: str,
        local_path: str,
        file_size_kb: float,
        download_date: str
    ) -> bool:
        """Records a successful download into the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO downloaded_addendums 
                (amc_id, amc_name, doc_title, doc_date, pdf_url, file_hash, download_date, local_filename, local_path, file_size_kb)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    amc_id,
                    amc_name,
                    doc_title,
                    doc_date,
                    pdf_url.strip(),
                    file_hash,
                    download_date,
                    local_filename,
                    local_path,
                    file_size_kb
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Already exists
                return False

    def get_downloads_for_date(self, download_date: str) -> List[Dict[str, Any]]:
        """Retrieves all downloads recorded for a specific date (YYYY-MM-DD)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM downloaded_addendums 
            WHERE download_date = ? 
            ORDER BY amc_name ASC, id ASC;
            """, (download_date,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def record_run(self, run_date: str, total_amcs: int, new_downloads: int, skipped: int, errors: int, summary_json: str = ""):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO run_history (run_date, total_amcs, new_downloads_count, skipped_count, errors_count, summary_json)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (run_date, total_amcs, new_downloads, skipped, errors, summary_json))
            conn.commit()
