#!/usr/bin/env python3
"""
Script to download ASDD (Absent/Shifted/Deceased) voter list data from CEO West Bengal website.
Uses Selenium to handle JavaScript-heavy pages.

IMPORTANT: Run this script on your local computer, not in a restricted environment.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
import time
import os
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


class ASDDSeleniumDownloader:
    def __init__(self, output_dir="asdd_data", headless=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.headless = headless
        self.url = "https://ceowestbengal.wb.gov.in/asd_sir"

        # Stats tracking
        self.stats = {
            'districts': 0,
            'constituencies': 0,
            'parts': 0,
            'downloaded': 0,
            'failed': 0
        }

        # Save progress
        self.progress_file = self.output_dir / "download_progress.json"
        self.progress = self.load_progress()

        self.driver = None

    def load_progress(self):
        """Load download progress from file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'completed': [], 'failed': []}

    def save_progress(self):
        """Save download progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def setup_driver(self):
        """Setup Chrome driver with download preferences"""
        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        # Set download directory
        prefs = {
            "download.default_directory": str(self.output_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        # Use webdriver-manager if available, otherwise use system chromedriver
        if WEBDRIVER_MANAGER_AVAILABLE:
            logger.info("Using webdriver-manager to setup ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            logger.info("Using system ChromeDriver (webdriver-manager not installed)...")
            self.driver = webdriver.Chrome(options=options)

        self.driver.implicitly_wait(10)
        logger.info("Browser driver initialized")

    def close_driver(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")

    def get_districts(self):
        """Extract all districts from dropdown"""
        logger.info("Fetching districts...")
        try:
            self.driver.get(self.url)
            time.sleep(3)  # Wait for page load

            # Click the "Download ASDD list" button to access the form
            try:
                logger.info("Looking for ASDD download button...")
                asdd_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//button[contains(text(), 'Download ASDD list by Assembly Constituency')]"))
                )
                asdd_button.click()
                logger.info("Clicked ASDD download button")
                time.sleep(2)  # Wait for form to appear
            except Exception as e:
                logger.warning(f"Could not find/click ASDD button: {e}")
                # Continue anyway, form might already be visible

            # Find district dropdown (correct ID is ddlDistrict)
            district_select = Select(self.driver.find_element(By.ID, "ddlDistrict"))
            districts = []

            for option in district_select.options:
                value = option.get_attribute("value")
                text = option.text.strip()

                if value and value != "" and text.lower() not in ['select', 'select district', '-- select district --']:
                    districts.append({
                        'value': value,
                        'name': text
                    })
                    logger.info(f"Found district: {text} ({value})")

            self.stats['districts'] = len(districts)
            return districts

        except Exception as e:
            logger.error(f"Error getting districts: {e}")
            return []

    def get_constituencies(self, district_value):
        """Get all assembly constituencies for a district"""
        try:
            # Select district (correct ID is ddlDistrict)
            district_select = Select(self.driver.find_element(By.ID, "ddlDistrict"))
            district_select.select_by_value(district_value)

            # Wait for constituency dropdown to populate
            time.sleep(2)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ddlAC"))
            )

            ac_select = Select(self.driver.find_element(By.ID, "ddlAC"))
            constituencies = []

            for option in ac_select.options:
                value = option.get_attribute("value")
                text = option.text.strip()

                if value and value != "" and text.lower() not in ['select', 'select assembly', '-- select ac --']:
                    constituencies.append({
                        'value': value,
                        'name': text
                    })

            logger.info(f"Found {len(constituencies)} constituencies")
            return constituencies

        except Exception as e:
            logger.error(f"Error getting constituencies: {e}")
            return []

    def get_parts(self, ac_value):
        """Get all parts for an assembly constituency"""
        try:
            # Select AC (correct ID is ddlAC)
            ac_select = Select(self.driver.find_element(By.ID, "ddlAC"))
            ac_select.select_by_value(ac_value)

            # Wait for part dropdown to populate
            time.sleep(2)

            # Try different possible IDs for part dropdown
            part_element = None
            for part_id in ["ddlPart", "part", "ddlPartNo"]:
                try:
                    part_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, part_id))
                    )
                    logger.info(f"Found part dropdown with ID: {part_id}")
                    break
                except:
                    continue

            if not part_element:
                logger.warning("Could not find part dropdown")
                return []

            part_select = Select(part_element)
            parts = []

            for option in part_select.options:
                value = option.get_attribute("value")
                text = option.text.strip()

                if value and value != "" and text.lower() not in ['select', 'select part', '-- select part --']:
                    parts.append({
                        'value': value,
                        'name': text
                    })

            logger.info(f"Found {len(parts)} parts")
            return parts

        except Exception as e:
            logger.error(f"Error getting parts: {e}")
            return []

    def download_part_data(self, district_name, ac_name, part_value, part_name):
        """Download data for a specific part"""
        try:
            # Find and select part dropdown
            part_element = None
            for part_id in ["ddlPart", "part", "ddlPartNo"]:
                try:
                    part_element = self.driver.find_element(By.ID, part_id)
                    break
                except:
                    continue

            if not part_element:
                logger.error("Could not find part dropdown for download")
                self.stats['failed'] += 1
                return False

            part_select = Select(part_element)
            part_select.select_by_value(part_value)

            time.sleep(1)

            # Look for download button/link
            # Try multiple strategies
            download_success = False

            try:
                # Strategy 1: Look for button with ID
                download_btn = self.driver.find_element(By.ID, "btnDownload")
                download_btn.click()
                download_success = True
            except NoSuchElementException:
                pass

            if not download_success:
                try:
                    # Strategy 2: Look for button with Download text
                    download_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Download') or contains(text(), 'DOWNLOAD')]")
                    download_btn.click()
                    download_success = True
                except NoSuchElementException:
                    pass

            if not download_success:
                try:
                    # Strategy 3: Look for link with PDF
                    download_link = self.driver.find_element(By.XPATH, "//a[contains(@href, '.pdf') or contains(text(), 'Download')]")
                    download_link.click()
                    download_success = True
                except NoSuchElementException:
                    pass

            if not download_success:
                logger.error(f"Could not find download button for part {part_name}")
                self.stats['failed'] += 1
                return False

            # Wait for download
            time.sleep(3)

            logger.info(f"Downloaded: {district_name} > {ac_name} > Part {part_name}")
            self.stats['downloaded'] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to download part {part_name}: {e}")
            self.stats['failed'] += 1
            return False

    def download_all(self, test_district=None):
        """Download all ASDD data"""
        try:
            self.setup_driver()

            districts = self.get_districts()

            if test_district:
                # Filter to only the test district
                districts = [d for d in districts if test_district.lower() in d['name'].lower()]
                logger.info(f"Testing with district: {districts[0]['name'] if districts else 'NOT FOUND'}")

            for district in districts:
                district_name = district['name']
                district_value = district['value']

                logger.info(f"\n{'='*60}")
                logger.info(f"Processing District: {district_name}")
                logger.info(f"{'='*60}")

                # Create district folder
                district_dir = self.output_dir / self.sanitize_filename(district_name)
                district_dir.mkdir(exist_ok=True)

                # Get constituencies
                constituencies = self.get_constituencies(district_value)
                self.stats['constituencies'] += len(constituencies)

                for ac in constituencies:
                    ac_name = ac['name']
                    ac_value = ac['value']

                    logger.info(f"\nProcessing AC: {ac_name}")

                    # Create AC folder
                    ac_dir = district_dir / self.sanitize_filename(ac_name)
                    ac_dir.mkdir(exist_ok=True)

                    # Get parts
                    parts = self.get_parts(ac_value)
                    self.stats['parts'] += len(parts)

                    for part in parts:
                        part_value = part['value']
                        part_name = part['name']

                        # Check if already downloaded
                        key = f"{district_name}|{ac_name}|{part_name}"
                        if key in self.progress['completed']:
                            logger.info(f"Skipping already downloaded: Part {part_name}")
                            continue

                        # Download
                        success = self.download_part_data(
                            district_name, ac_name, part_value, part_name
                        )

                        if success:
                            self.progress['completed'].append(key)
                        else:
                            self.progress['failed'].append(key)

                        self.save_progress()

                        # Be polite to the server
                        time.sleep(1)

                    # Go back to main page after each AC
                    self.driver.get(self.url)
                    time.sleep(2)

        finally:
            self.close_driver()
            self.print_stats()

    def sanitize_filename(self, filename):
        """Clean filename for safe filesystem usage"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

    def print_stats(self):
        """Print download statistics"""
        logger.info("\n" + "="*60)
        logger.info("Download Statistics")
        logger.info("="*60)
        logger.info(f"Districts processed: {self.stats['districts']}")
        logger.info(f"Constituencies processed: {self.stats['constituencies']}")
        logger.info(f"Parts processed: {self.stats['parts']}")
        logger.info(f"Files downloaded: {self.stats['downloaded']}")
        logger.info(f"Failed downloads: {self.stats['failed']}")
        logger.info("="*60)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Download ASDD data from CEO West Bengal website'
    )
    parser.add_argument(
        '--test-district',
        type=str,
        help='Test with a specific district (e.g., "Malda")',
        default=None
    )
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='Show browser window (not headless)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='asdd_data',
        help='Output directory for downloaded files'
    )

    args = parser.parse_args()

    downloader = ASDDSeleniumDownloader(
        output_dir=args.output_dir,
        headless=not args.show_browser
    )

    downloader.download_all(test_district=args.test_district)


if __name__ == "__main__":
    main()
