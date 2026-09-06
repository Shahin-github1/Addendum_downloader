import os
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from .date_utils import get_app_root

class ExcelReporter:
    def __init__(self, base_download_dir: str = None):
        if base_download_dir is None:
            base_dir = get_app_root()
            base_download_dir = os.path.join(base_dir, "downloads")
        self.base_download_dir = base_download_dir

    def generate_report(self, day_folder_name: str, records: List[Dict[str, Any]]) -> str:
        """
        Generates a formatted Excel file inside:
        downloads/{day_folder_name}/Addendum_Summary_{day_folder_name}.xlsx
        """
        target_dir = os.path.join(self.base_download_dir, day_folder_name)
        os.makedirs(target_dir, exist_ok=True)
        safe_name = day_folder_name.replace(" ", "_")
        excel_path = os.path.join(target_dir, f"Addendum_Summary_{safe_name}.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "Addendums"

        headers = [
            "Sl No.",
            "AMC Name",
            "Document Title",
            "Publication Date",
            "Original Download Link",
            "Downloaded File Name",
            "File Size (KB)",
            "Download Timestamp",
            "Status"
        ]

        # Header styling
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.append(headers)
        ws.row_dimensions[1].height = 28

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # Thin borders
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        alt_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
        link_font = Font(name="Calibri", size=10, color="0563C1", underline="single")
        default_font = Font(name="Calibri", size=10)

        for i, row in enumerate(records, start=1):
            row_idx = i + 1
            ws.row_dimensions[row_idx].height = 20

            url = row.get("pdf_url", "")
            title = row.get("doc_title", "N/A")
            size_kb = row.get("file_size_kb", 0.0)

            ws.append([
                i,
                row.get("amc_name", ""),
                title,
                row.get("doc_date", ""),
                url,
                row.get("local_filename", ""),
                size_kb if size_kb else "-",
                row.get("download_date", ""),
                row.get("status", "Downloaded")
            ])

            # Apply alternating row background & borders
            is_alt = (i % 2 == 0)
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = thin_border
                cell.font = default_font
                if is_alt:
                    cell.fill = alt_fill

                # Hyperlink for URL column (Column 5)
                if col_idx == 5 and url and url.startswith("http"):
                    cell.font = link_font
                    cell.hyperlink = url

                if col_idx in (1, 4, 7, 8, 9):
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # Auto-fit column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or '')
                if cell.column == 5 and len(val) > 40:
                    val = val[:40]  # Cap link width
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        wb.save(excel_path)
        return excel_path
