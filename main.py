"""
Main Application and CLI Menu with Interactive Failure Options:
[1] Retry Current Passport
[2] Skip Current Passport
[3] Stop Automation
"""
import sys
from config import EXCEL_PATH
from logger import setup_logger, mask_passport
from excel_manager import ExcelManager
from browser_manager import BrowserManager
from security_manager import SecurityManager
from wafid_automation import WafidAutomation

logger = setup_logger("Main")

class WafidApp:
    def __init__(self):
        self.excel_mgr = ExcelManager()
        self.browser_mgr = BrowserManager()
        self.driver = None
        self.dry_run = False

    def run_cli(self):
        while True:
            print("\n" + "="*50)
            print("WAFID MEDICAL DATA EXTRACTION & EXCEL AUTOMATION")
            print("="*50)
            print("[1] Start automation")
            print("[2] Check Excel workbook")
            print("[3] Verify website login session")
            print("[4] View execution summary")
            print("[5] Toggle Dry Run Mode (Current: {})".format("ON" if self.dry_run else "OFF"))
            print("[6] Exit")
            print("="*50)

            choice = input("Select an option (1-6): ").strip()

            if choice == "1":
                self.start_automation_workflow()
            elif choice == "2":
                self.check_workbook()
            elif choice == "3":
                self.verify_login_workflow()
            elif choice == "4":
                print("\nExecution summary requires running automation first.")
            elif choice == "5":
                self.dry_run = not self.dry_run
                print(f"Dry Run Mode is now {'ON' if self.dry_run else 'OFF'}")
            elif choice == "6":
                print("Exiting application. Goodbye!")
                if self.driver:
                    self.browser_mgr.close_browser()
                sys.exit(0)
            else:
                print("Invalid selection. Please choose between 1 and 6.")

    def check_workbook(self):
        try:
            records = self.excel_mgr.get_records()
            print(f"\nWorkbook loaded successfully from {EXCEL_PATH}")
            print(f"Total populated records found: {len(records)}")
            duplicates = self.excel_mgr.detect_duplicates()
            if duplicates:
                print(f"WARNING: Duplicate passport entries detected: {len(duplicates)}")
            else:
                print("No duplicate passports detected.")
        except Exception as e:
            print(f"Error checking workbook: {e}")

    def ensure_authenticated_session(self) -> bool:
        if self.dry_run:
            return True

        if not self.driver:
            self.driver = self.browser_mgr.start_browser()

        if self.browser_mgr.check_authenticated_session():
            print("Persistent Wafid login session is active. Proceeding automatically.")
            return True

        user_wants_login = SecurityManager.prompt_manual_login_required()
        if not user_wants_login:
            return False

        SecurityManager.wait_for_manual_login_completion()
        return self.browser_mgr.check_authenticated_session()

    def verify_login_workflow(self):
        try:
            is_active = self.ensure_authenticated_session()
            if is_active:
                print("Wafid login session is active and ready.")
            else:
                print("Session verification incomplete.")
        except Exception as e:
            print(f"Error during login verification: {e}")

    def prompt_failure_action(self, passport: str, row: int) -> str:
        """
        Interactive CMD menu displayed on search or extraction failure.
        """
        print("\n" + "!"*50)
        print(f"FAILURE OCCURRED FOR PASSPORT {mask_passport(passport)} (Row {row})")
        print("!"*50)
        print("[1] Retry Current Passport")
        print("[2] Skip Current Passport")
        print("[3] Stop Automation")
        print("!"*50)
        
        while True:
            choice = input("Select an option (1-3): ").strip()
            if choice in ["1", "2", "3"]:
                return choice
            print("Invalid choice. Please enter 1, 2, or 3.")

    def start_automation_workflow(self):
        summary = {
            "total": 0, "processed": 0, "success": 0, "fit": 0,
            "unfit": 0, "expired": 0, "skipped": 0, "net_error": 0, "invalid": 0
        }

        try:
            records = self.excel_mgr.get_records()
            summary["total"] = len(records)
            if not records:
                print("No records found in Excel workbook.")
                return

            self.excel_mgr.create_backup()

            if not self.ensure_authenticated_session():
                print("Automation aborted: Wafid session not authenticated.")
                return

            wafid_auto = WafidAutomation(self.driver)

            i = 0
            while i < len(records):
                rec = records[i]
                row = rec["row"]
                passport = rec["passport"]
                status = rec["status"].lower()

                if self.excel_mgr.is_row_completed(row):
                    logger.info(f"Row {row} already completed. Skipping.")
                    summary["skipped"] += 1
                    i += 1
                    continue

                masked_p = mask_passport(passport)
                print(f"\nProcessing Row {row} | Passport: {masked_p} | Status: {status.upper()}")

                if status == "expired":
                    summary["expired"] += 1
                    self.excel_mgr.write_result(row, {}, "expired")
                    print("Status is Expired. Wrote '-' into columns E and F.")
                    i += 1
                    continue

                if status not in ["fit", "unfit"]:
                    summary["invalid"] += 1
                    print(f"Unknown or empty status '{status}'. Marking for manual review.")
                    i += 1
                    continue

                is_unfit = (status == "unfit")

                # Perform Search
                search_success = wafid_auto.search_passport(passport, dry_run=self.dry_run)

                if not search_success:
                    action = self.prompt_failure_action(passport, row)
                    if action == "1":
                        logger.info(f"User selected RETRY for passport {masked_p} (Row {row}).")
                        continue  # Repeat loop at same index i
                    elif action == "2":
                        logger.info(f"User selected SKIP for passport {masked_p} (Row {row}).")
                        summary["net_error"] += 1
                        self.excel_mgr.write_error(row, "NETERROR")
                        i += 1
                        continue
                    elif action == "3":
                        logger.info(f"User selected STOP AUTOMATION at row {row}.")
                        print("Automation stopped by user.")
                        break

                try:
                    extracted_data = wafid_auto.open_and_extract_report(is_unfit=is_unfit, dry_run=self.dry_run)
                    self.excel_mgr.write_result(row, extracted_data, status)
                    
                    summary["success"] += 1
                    if is_unfit:
                        summary["unfit"] += 1
                    else:
                        summary["fit"] += 1

                    wafid_auto.close_report_by_outside_click(dry_run=self.dry_run)
                    i += 1  # Successfully completed, move to next passport

                except Exception as e:
                    logger.error(f"Extraction failed for row {row}: {e}")
                    wafid_auto.close_report_by_outside_click(dry_run=self.dry_run)
                    
                    action = self.prompt_failure_action(passport, row)
                    if action == "1":
                        logger.info(f"User selected RETRY for passport {masked_p} (Row {row}).")
                        continue  # Repeat loop at same index i
                    elif action == "2":
                        logger.info(f"User selected SKIP for passport {masked_p} (Row {row}).")
                        summary["invalid"] += 1
                        self.excel_mgr.write_error(row, "EXTERROR")
                        i += 1
                        continue
                    elif action == "3":
                        logger.info(f"User selected STOP AUTOMATION at row {row}.")
                        print("Automation stopped by user.")
                        break

            print("\n" + "="*40)
            print("AUTOMATION EXECUTION SUMMARY")
            print("="*40)
            for k, v in summary.items():
                print(f"  {k.capitalize()}: {v}")
            print("="*40)

        except Exception as e:
            logger.error(f"Automation workflow interrupted: {e}")
            print(f"Error during automation: {e}")

if __name__ == "__main__":
    app = WafidApp()
    app.run_cli()