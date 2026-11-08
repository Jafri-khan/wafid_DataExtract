"""
Edge Browser Manager using Selenium WebDriver with persistent user data profile support and profile-lock handling.
"""
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from config import WAFID_BASE_URL, DEFAULT_TIMEOUT, EDGE_PROFILE_DIR, BASE_DIR
from logger import setup_logger

logger = setup_logger("BrowserManager")

class BrowserManager:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None

    def start_browser(self):
        if self.driver is not None:
            return self.driver

        try:
            options = webdriver.EdgeOptions()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # Persistent Profile Configuration
            profile_dir = EDGE_PROFILE_DIR
            profile_dir.mkdir(parents=True, exist_ok=True)
            user_data_path = str(profile_dir.resolve())
            
            options.add_argument(f"--user-data-dir={user_data_path}")
            options.add_argument("--profile-directory=Default")

            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=options)
            self.driver.set_page_load_timeout(DEFAULT_TIMEOUT)
            
            logger.info("Microsoft Edge WebDriver initialized with persistent profile.")
            return self.driver
        except Exception as e:
            err_msg = str(e)
            if "user data directory is already in use" in err_msg.lower() or "singletonlock" in err_msg.lower() or "devtoolsactiveport" in err_msg.lower():
                print("\n" + "="*65)
                print("ERROR: Edge Profile is Already in Use / Locked!")
                print("="*65)
                print(f"The profile directory '{EDGE_PROFILE_DIR}' is locked by another instance of Edge.")
                print("Please close any open Microsoft Edge windows or background msedgedriver processes")
                print("using Task Manager, then restart the application.")
                print("="*65)
                logger.error("Edge profile directory is already locked by another process.")
            else:
                logger.error(f"Failed to start Edge browser with persistent profile: {e}")
            raise

    def check_authenticated_session(self) -> bool:
        try:
            if not self.driver:
                self.start_browser()
            
            self.driver.get(WAFID_BASE_URL)
            page_src = self.driver.page_source.lower()
            
            # Check if login required indicators are present (e.g., login button or lack of input#id_passport)
            # Wafid search page contains input#id_passport when authenticated/search-ready.
            if "id_passport" in page_src or "logout" in page_src:
                logger.info("Existing authenticated session detected.")
                return True

            logger.info("No active authenticated session detected.")
            return False
        except Exception as e:
            logger.warning(f"Error while checking active session: {e}")
            return False

    def close_browser(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully.")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None
