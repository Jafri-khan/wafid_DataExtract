"""
Wafid website automation module handling field clearing, search, notepad icon check, outside-click modal closure, and return to search page.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES, WAFID_BASE_URL
from logger import setup_logger, mask_passport
from data_extractor import DataExtractor

logger = setup_logger("WafidAutomation")

class WafidAutomation:
    def __init__(self, driver):
        self.driver = driver

    def clear_and_enter_passport(self, passport_number: str) -> bool:
        try:
            input_elem = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input#id_passport"))
            )
            input_elem.click()
            input_elem.send_keys(Keys.CONTROL + "a")
            input_elem.send_keys(Keys.BACKSPACE)
            
            current_val = input_elem.get_attribute("value")
            if current_val != "":
                input_elem.clear()

            input_elem.send_keys(passport_number)
            entered_val = input_elem.get_attribute("value")
            if entered_val != passport_number:
                logger.error(f"Passport mismatch. Expected {passport_number}, got {entered_val}")
                return False

            return True
        except Exception as e:
            logger.error(f"Error clearing and entering passport field: {e}")
            return False

    def check_and_handle_notepad(self) -> bool:
        """
        Checks if the notepad icon appears on the current page:
        <div class="image icon"><img src="/static/svg/notepad.svg"></div>
        If present, clicks it (or its nearest clickable parent) using explicit waits and verifies new page load.
        """
        try:
            notepad_xpath = "//img[contains(@src, 'notepad.svg')]"
            elems = self.driver.find_elements(By.XPATH, notepad_xpath)
            
            if not elems or not elems[0].is_displayed():
                return False

            logger.info("Notepad option detected on page. Handling click...")
            img_elem = elems[0]
            
            target_elem = img_elem
            for _ in range(3):
                parent = target_elem.find_element(By.XPATH, "./ancestor::*[self::a or self::button or self::div[@class='image icon']][1]")
                if parent:
                    target_elem = parent
                else:
                    break

            WebDriverWait(self.driver, 5).until(lambda d: target_elem.is_enabled())
            
            actions = ActionChains(self.driver)
            actions.move_to_element(target_elem).click().perform()
            actions.reset_actions()

            WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logger.info("Notepad page loaded and verified successfully.")
            return True

        except TimeoutException:
            logger.warning("Timeout waiting for notepad page to load.")
            return False
        except Exception as e:
            logger.info(f"Notepad option not present or skipped: {e}")
            return False

    def search_passport(self, passport_number: str, dry_run: bool = False) -> bool:
        masked = mask_passport(passport_number)
        if dry_run:
            logger.info(f"[DRY RUN] Simulated search for passport: {masked}")
            time.sleep(1)
            return True

        for attempt in range(1, DEFAULT_MAX_RETRIES + 1):
            try:
                logger.info(f"Attempt {attempt}: Entering passport {masked}")
                
                if not self.clear_and_enter_passport(passport_number):
                    raise ValueError("Failed to prepare passport input field.")

                search_btn = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ui.primary.large.submit.button"))
                )
                search_btn.click()

                time.sleep(1)
                self.check_and_handle_notepad()

                WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "i.eye.big.slip-view-icon-js.icon"))
                )
                logger.info("Search executed and result loaded.")
                return True

            except (TimeoutException, NoSuchElementException) as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt == DEFAULT_MAX_RETRIES:
                    logger.error("Max retries reached for passport search.")
                    return False
                time.sleep(2)
            except Exception as e:
                logger.error(f"Unexpected search error: {e}")
                return False
        return False

    def open_and_extract_report(self, is_unfit: bool, dry_run: bool = False) -> dict:
        if dry_run:
            return {
                "exam_date": "15-10-2026",
                "height": "171.0 Cms",
                "weight": "55.0 Kgs",
                "blood_group": "B+",
                "hemoglobin": "15.1",
                "rbs": "102.0",
                "creatinine": "1.0",
                "remarks": "CALCIFICATION" if is_unfit else "-"
            }

        try:
            self.check_and_handle_notepad()

            eye_icon = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "i.eye.big.slip-view-icon-js.icon"))
            )
            eye_icon.click()

            full_report_btn = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ui.button.primary.full-report-button-js"))
            )
            full_report_btn.click()

            time.sleep(2)
            html_content = self.driver.page_source
            return DataExtractor.parse_report_html(html_content, is_unfit)

        except Exception as e:
            logger.error(f"Error opening/extracting report: {e}")
            raise

    def close_report_by_outside_click(self, dry_run: bool = False):
        if dry_run:
            return

        try:
            logger.info("Attempting to close report modal via outside click on dimmed background...")
            
            modal_selectors = [
                "div.ui.modal", 
                "div.full-report-container", 
                "div.dialog", 
                "div.ui.standard.modal",
                ".full-report-content-js"
            ]
            
            modal_elem = None
            for sel in modal_selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in elems:
                        if el.is_displayed():
                            modal_elem = el
                            break
                    if modal_elem:
                        break
                except Exception:
                    continue

            actions = ActionChains(self.driver)

            if modal_elem:
                loc = modal_elem.location
                size = modal_elem.size
                
                modal_x = loc['x']
                modal_y = loc['y']
                
                target_x = max(10, modal_x - 60)
                target_y = max(10, modal_y - 60)
                
                logger.info(f"Calculated outside click position at offset x={target_x}, y={target_y}")
                actions.move_by_offset(target_x, target_y).click().perform()
                actions.reset_actions()
            else:
                logger.warning("Modal element not explicitly isolated; clicking top-left viewport background.")
                actions.move_by_offset(30, 30).click().perform()
                actions.reset_actions()

            time.sleep(1.5)
            
            input_elem = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input#id_passport"))
            )
            input_elem.click()
            input_elem.send_keys(Keys.CONTROL + "a")
            input_elem.send_keys(Keys.BACKSPACE)
            
            val = input_elem.get_attribute("value")
            if val != "":
                input_elem.clear()
                
            logger.info("Successfully closed report modal via outside click and reset passport input.")

        except Exception as e:
            logger.warning(f"Outside click attempt encountered issue ({e}), attempting fallback navigation...")
            try:
                self.driver.get(WAFID_BASE_URL)
                input_elem = WebDriverWait(self.driver, DEFAULT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input#id_passport"))
                )
                input_elem.click()
                input_elem.send_keys(Keys.CONTROL + "a")
                input_elem.send_keys(Keys.BACKSPACE)
                logger.info("Fallback navigation to search page completed successfully.")
            except Exception as ex:
                logger.error(f"Failed fallback navigation to search page: {ex}")
                raise
