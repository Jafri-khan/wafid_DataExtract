"""
Excel Manager with exact cell mapping (E-L) and strict per-record instant saving.
"""
import shutil
from datetime import datetime
import openpyxl
from config import (
    EXCEL_PATH, BACKUP_DIR, COL_PASSPORT, COL_STATUS,
    COL_EXAM_DATE, COL_HEIGHT, COL_WEIGHT, COL_BLOOD, COL_HEMOGLOBIN,
    COL_RBS, COL_CREATININE, COL_REMARKS
)
from logger import setup_logger

logger = setup_logger("ExcelManager")

class ExcelManager:
    def __init__(self, excel_path=EXCEL_PATH):
        self.excel_path = excel_path

    def create_backup(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"Datatocheck_backup_{timestamp}.xlsx"
        try:
            shutil.copy2(self.excel_path, backup_file)
            logger.info(f"Backup created successfully at {backup_file}")
            return str(backup_file)
        except Exception as e:
            logger.error(f"Failed to create workbook backup: {e}")
            raise

    def load_workbook(self):
        try:
            wb = openpyxl.load_workbook(self.excel_path)
            sheet = wb.active
            return wb, sheet
        except Exception as e:
            logger.error(f"Failed to load Excel workbook: {e}")
            raise

    def get_records(self, start_row=2, end_row=None):
        wb, sheet = self.load_workbook()
        records = []
        max_row = end_row or sheet.max_row

        for row in range(start_row, max_row + 1):
            passport = sheet.cell(row=row, column=COL_PASSPORT).value
            status = sheet.cell(row=row, column=COL_STATUS).value

            if passport is not None or status is not None:
                records.append({
                    "row": row,
                    "passport": str(passport).strip() if passport else "",
                    "status": str(status).strip() if status else ""
                })
        wb.close()
        return records

    def write_result(self, row: int, data: dict, status: str):
        wb, sheet = self.load_workbook()
        try:
            if status.lower() == "expired":
                sheet.cell(row=row, column=COL_EXAM_DATE).value = "-"
                sheet.cell(row=row, column=COL_HEIGHT).value = "-"
            else:
                sheet.cell(row=row, column=COL_EXAM_DATE).value = data.get("exam_date", "")
                sheet.cell(row=row, column=COL_HEIGHT).value = data.get("height", "")
                sheet.cell(row=row, column=COL_WEIGHT).value = data.get("weight", "")
                sheet.cell(row=row, column=COL_BLOOD).value = data.get("blood_group", "")
                sheet.cell(row=row, column=COL_HEMOGLOBIN).value = data.get("hemoglobin", "")
                sheet.cell(row=row, column=COL_RBS).value = data.get("rbs", "")
                sheet.cell(row=row, column=COL_CREATININE).value = data.get("creatinine", "")
                sheet.cell(row=row, column=COL_REMARKS).value = data.get("remarks", "-")
            
            wb.save(self.excel_path)
            logger.info(f"Successfully saved record to row {row} in {self.excel_path}")
            self._verify_saved_data(row, data, status)
        except Exception as e:
            logger.error(f"Error writing to Excel row {row}: {e}")
            raise
        finally:
            wb.close()

    def _verify_saved_data(self, row: int, data: dict, status: str):
        wb, sheet = self.load_workbook()
        try:
            if status.lower() == "expired":
                val = sheet.cell(row=row, column=COL_HEIGHT).value
                assert val == "-", f"Verification failed for expired status at row {row}"
            else:
                h_val = sheet.cell(row=row, column=COL_HEIGHT).value
                w_val = sheet.cell(row=row, column=COL_WEIGHT).value
                assert h_val == data.get("height", ""), f"Height mismatch at row {row}"
                assert w_val == data.get("weight", ""), f"Weight mismatch at row {row}"
            logger.info(f"Verification confirmed for row {row}")
        finally:
            wb.close()

    def write_error(self, row: int, error_code: str):
        wb, sheet = self.load_workbook()
        try:
            sheet.cell(row=row, column=COL_HEIGHT).value = error_code
            wb.save(self.excel_path)
            logger.warning(f"Wrote error code {error_code} to row {row}")
        except Exception as e:
            logger.error(f"Error writing error code to row {row}: {e}")
        finally:
            wb.close()

    def is_row_completed(self, row: int) -> bool:
        wb, sheet = self.load_workbook()
        try:
            val = sheet.cell(row=row, column=COL_HEIGHT).value
            wb.close()
            return val is not None and str(val).strip() != ""
        except Exception:
            wb.close()
            return False

    def detect_duplicates(self) -> list:
        records = self.get_records()
        seen = set()
        duplicates = []
        for r in records:
            p = r["passport"]
            if p and p != "":
                if p in seen:
                    duplicates.append(p)
                else:
                    seen.add(p)
        return duplicates
