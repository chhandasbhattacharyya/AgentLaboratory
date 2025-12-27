#!/usr/bin/env python3
"""
Semi-automated ASDD downloader - pauses for manual CAPTCHA solving
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
import time
from pathlib import Path
import logging
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('asdd_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ASDDManualDownloader:
    def __init__(self, output_dir="asdd_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.url = "https://ceowestbengal.wb.gov.in/asd_sir"
        self.driver = None

        # Stats tracking
        self.stats = {
            'districts': 0,
            'constituencies': 0,
            'polling_stations': 0
        }

    def setup_driver(self):
        """Setup Chrome driver - NOT headless so user can solve CAPTCHA"""
        options = webdriver.ChromeOptions()

        # IMPORTANT: Not headless - user needs to see and solve CAPTCHA
        # options.add_argument('--headless')  # DISABLED

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')

        # Set download directory
        prefs = {
            "download.default_directory": str(self.output_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        if WEBDRIVER_MANAGER_AVAILABLE:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        self.driver.implicitly_wait(10)
        logger.info("Browser driver initialized")

    def wait_for_user(self, message, seconds=30):
        """Wait for user to perform manual action"""
        print("\n" + "="*60)
        print(f"⚠️  MANUAL ACTION REQUIRED:")
        print(f"   {message}")
        print(f"   You have {seconds} seconds...")
        print("="*60)

        for i in range(seconds, 0, -1):
            print(f"\rContinuing in {i} seconds... ", end='', flush=True)
            time.sleep(1)
        print("\n✓ Continuing...\n")

    def navigate_and_select(self, district_name=None):
        """Navigate to the page and let user select district/AC manually"""
        try:
            self.setup_driver()

            self.driver.get(self.url)
            time.sleep(3)

            # Click ASDD button
            try:
                asdd_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//button[contains(text(), 'Download ASDD list by Assembly Constituency')]"))
                )
                asdd_button.click()
                logger.info("Clicked ASDD download button")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not find ASDD button: {e}")

            # Let user select district and AC manually
            self.wait_for_user(
                "Please select District and Assembly Constituency from the dropdowns",
                seconds=15
            )

            # List all download buttons
            download_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Download')]")

            if not download_buttons:
                download_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Download')]")

            logger.info(f"Found {len(download_buttons)} polling stations")

            print("\n" + "="*60)
            print(f"INSTRUCTIONS:")
            print(f"  Total polling stations: {len(download_buttons)}")
            print(f"  The script will click each Download button")
            print(f"  If a CAPTCHA appears, SOLVE IT MANUALLY")
            print(f"  The script will wait 10 seconds after each download")
            print("="*60)

            input("\nPress ENTER when ready to start downloading...")

            # Download each polling station
            for i in range(len(download_buttons)):
                # Re-find buttons (DOM might refresh)
                download_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Download')]")
                if not download_buttons:
                    download_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Download')]")

                if i >= len(download_buttons):
                    logger.warning(f"Button {i+1} no longer available")
                    continue

                button = download_buttons[i]

                try:
                    logger.info(f"Downloading polling station #{i+1}...")
                    button.click()

                    # Wait longer to give user time to solve CAPTCHA if it appears
                    print(f"⏳ Waiting 10 seconds (solve CAPTCHA if it appears)...")
                    time.sleep(10)

                    logger.info(f"✓ Downloaded PS #{i+1}")
                    self.stats['polling_stations'] += 1

                except Exception as e:
                    logger.error(f"Error on PS #{i+1}: {e}")

                    # Ask user what to do
                    print("\n❌ Error occurred!")
                    print("Options:")
                    print("  1. Press ENTER to skip this and continue")
                    print("  2. Type 'retry' to try again")
                    print("  3. Type 'stop' to stop")

                    choice = input("Your choice: ").strip().lower()

                    if choice == 'stop':
                        logger.info("User requested stop")
                        break
                    elif choice == 'retry':
                        try:
                            button.click()
                            time.sleep(10)
                            logger.info(f"✓ Downloaded PS #{i+1} (retry)")
                        except:
                            logger.error(f"Retry failed for PS #{i+1}")

            print("\n" + "="*60)
            print("Download Complete!")
            print(f"Downloaded {self.stats['polling_stations']} polling stations")
            print(f"Files saved to: {self.output_dir.absolute()}")
            print("="*60)

            input("\nPress ENTER to close browser...")

        finally:
            if self.driver:
                self.driver.quit()


def main():
    print("="*60)
    print("ASDD Semi-Automated Downloader")
    print("(Requires manual CAPTCHA solving)")
    print("="*60)

    downloader = ASDDManualDownloader(output_dir='asdd_data')
    downloader.navigate_and_select()


if __name__ == "__main__":
    main()
