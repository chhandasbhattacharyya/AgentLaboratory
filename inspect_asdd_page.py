#!/usr/bin/env python3
"""
Diagnostic script to inspect the ASDD website structure and find the correct element selectors.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
import time
from pathlib import Path

def inspect_page():
    """Inspect the ASDD page and save its structure"""

    # Setup Chrome driver
    options = webdriver.ChromeOptions()
    # Don't use headless so you can see what's happening
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    # Initialize driver
    if WEBDRIVER_MANAGER_AVAILABLE:
        print("Using webdriver-manager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    else:
        print("Using system ChromeDriver...")
        driver = webdriver.Chrome(options=options)

    try:
        url = "https://ceowestbengal.wb.gov.in/asd_sir"
        print(f"\nNavigating to {url}...")
        driver.get(url)

        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(5)

        # Save page source
        page_source = driver.page_source
        output_file = Path("asdd_page_source.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"✓ Saved page source to: {output_file}")

        # Find all select elements
        print("\n" + "="*60)
        print("FINDING ALL SELECT/DROPDOWN ELEMENTS:")
        print("="*60)
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"Found {len(selects)} select elements\n")

        for i, select in enumerate(selects, 1):
            select_id = select.get_attribute('id')
            select_name = select.get_attribute('name')
            select_class = select.get_attribute('class')

            print(f"Select #{i}:")
            print(f"  ID: {select_id}")
            print(f"  Name: {select_name}")
            print(f"  Class: {select_class}")

            # Get options
            options_elements = select.find_elements(By.TAG_NAME, "option")
            print(f"  Options count: {len(options_elements)}")

            if len(options_elements) <= 20:
                print("  First few options:")
                for opt in options_elements[:10]:
                    value = opt.get_attribute('value')
                    text = opt.text.strip()
                    print(f"    - value='{value}', text='{text}'")
            print()

        # Find all buttons
        print("\n" + "="*60)
        print("FINDING ALL BUTTONS:")
        print("="*60)
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Found {len(buttons)} button elements\n")

        for i, btn in enumerate(buttons, 1):
            btn_id = btn.get_attribute('id')
            btn_class = btn.get_attribute('class')
            btn_text = btn.text.strip()
            btn_type = btn.get_attribute('type')

            print(f"Button #{i}:")
            print(f"  ID: {btn_id}")
            print(f"  Class: {btn_class}")
            print(f"  Type: {btn_type}")
            print(f"  Text: {btn_text}")
            print()

        # Find all links
        print("\n" + "="*60)
        print("FINDING DOWNLOAD LINKS:")
        print("="*60)
        links = driver.find_elements(By.TAG_NAME, "a")
        download_links = [link for link in links if 'download' in link.get_attribute('href').lower() or 'download' in link.text.lower()]
        print(f"Found {len(download_links)} potential download links\n")

        for i, link in enumerate(download_links[:10], 1):
            href = link.get_attribute('href')
            text = link.text.strip()
            print(f"Link #{i}:")
            print(f"  Href: {href}")
            print(f"  Text: {text}")
            print()

        # Find all input elements
        print("\n" + "="*60)
        print("FINDING ALL INPUT ELEMENTS:")
        print("="*60)
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} input elements\n")

        for i, inp in enumerate(inputs[:20], 1):
            inp_id = inp.get_attribute('id')
            inp_name = inp.get_attribute('name')
            inp_type = inp.get_attribute('type')
            inp_class = inp.get_attribute('class')

            print(f"Input #{i}:")
            print(f"  ID: {inp_id}")
            print(f"  Name: {inp_name}")
            print(f"  Type: {inp_type}")
            print(f"  Class: {inp_class}")
            print()

        print("\n" + "="*60)
        print("INSPECTION COMPLETE!")
        print("="*60)
        print(f"\nPage source saved to: {output_file.absolute()}")
        print("\nNow:")
        print("1. Open 'asdd_page_source.html' in a text editor")
        print("2. Look for the district/AC/part dropdown elements")
        print("3. Note their IDs, names, or classes")
        print("4. Share that information to update the script")

        # Keep browser open for 30 seconds so user can inspect
        print("\nBrowser will stay open for 30 seconds for manual inspection...")
        time.sleep(30)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\nBrowser closed.")

if __name__ == "__main__":
    inspect_page()
