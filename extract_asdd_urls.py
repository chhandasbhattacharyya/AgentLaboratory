#!/usr/bin/env python3
"""
Extract ASDD download URLs without clicking (to avoid CAPTCHA)
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
import csv
from pathlib import Path

def extract_urls():
    """Extract all download URLs and save to CSV"""

    # Setup driver
    options = webdriver.ChromeOptions()
    # Keep visible so you can manually select district/AC
    options.add_argument('--window-size=1920,1080')

    if WEBDRIVER_MANAGER_AVAILABLE:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    try:
        url = "https://ceowestbengal.wb.gov.in/asd_sir"
        driver.get(url)
        time.sleep(3)

        # Click ASDD button
        try:
            asdd_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(text(), 'Download ASDD list by Assembly Constituency')]"))
            )
            asdd_button.click()
            time.sleep(2)
        except Exception as e:
            print(f"Could not click ASDD button: {e}")

        print("\n" + "="*60)
        print("INSTRUCTIONS:")
        print("1. Select District from dropdown")
        print("2. Select Assembly Constituency from dropdown")
        print("3. Wait for table to load")
        print("="*60)

        input("\nPress ENTER when table is loaded...")

        # Find all download buttons and extract information
        rows = driver.find_elements(By.XPATH, "//table//tr")

        data = []
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    ps_no = cells[0].text.strip()
                    ps_name = cells[1].text.strip()

                    # Try to find download link
                    download_btn = cells[2].find_element(By.XPATH, ".//button | .//a")
                    onclick = download_btn.get_attribute('onclick')
                    href = download_btn.get_attribute('href')

                    data.append({
                        'PS_No': ps_no,
                        'Polling_Station': ps_name,
                        'OnClick': onclick or '',
                        'Href': href or ''
                    })

                    print(f"PS {ps_no}: {ps_name}")
            except:
                continue

        # Save to CSV
        output_file = Path('asdd_urls.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=['PS_No', 'Polling_Station', 'OnClick', 'Href'])
                writer.writeheader()
                writer.writerows(data)

        print(f"\n✓ Saved {len(data)} entries to {output_file}")
        print("\nNow you can:")
        print("1. Review the CSV file")
        print("2. Use the onclick/href information to download manually")

        input("\nPress ENTER to close...")

    finally:
        driver.quit()


if __name__ == "__main__":
    extract_urls()
