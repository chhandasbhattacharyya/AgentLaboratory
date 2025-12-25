#!/usr/bin/env python3
"""
Test script to understand the ASDD website structure
"""

import requests
from bs4 import BeautifulSoup
import json

# Setup session with proper headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://ceowestbengal.wb.gov.in/',
})

url = "https://ceowestbengal.wb.gov.in/asd_sir"

print("Attempting to fetch the ASDD page...")
try:
    response = session.get(url, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.content)} bytes")

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Save the HTML
        with open('asdd_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("✓ Saved page to asdd_page.html")

        # Look for select/dropdown elements
        print("\n=== SELECT ELEMENTS ===")
        selects = soup.find_all('select')
        for select in selects:
            select_id = select.get('id', 'no-id')
            select_name = select.get('name', 'no-name')
            print(f"\nSelect: id='{select_id}', name='{select_name}'")
            options = select.find_all('option')
            print(f"  Options count: {len(options)}")
            if len(options) <= 30:  # Only print if not too many
                for opt in options[:10]:  # First 10
                    print(f"    - value='{opt.get('value')}', text='{opt.get_text().strip()}'")

        # Look for forms
        print("\n=== FORMS ===")
        forms = soup.find_all('form')
        for form in forms:
            print(f"Form: action='{form.get('action')}', method='{form.get('method')}'")

        # Look for links
        print("\n=== DOWNLOAD LINKS ===")
        links = soup.find_all('a', href=lambda x: x and ('.pdf' in x.lower() or 'download' in x.lower()))
        print(f"Found {len(links)} PDF/download links")
        for link in links[:5]:
            print(f"  - {link.get('href')} : {link.get_text().strip()[:50]}")

        # Look for JavaScript/AJAX endpoints
        print("\n=== SCRIPTS ===")
        scripts = soup.find_all('script')
        print(f"Found {len(scripts)} script tags")

        # Look for API endpoints in scripts
        for script in scripts:
            if script.string:
                if 'ajax' in script.string.lower() or 'api' in script.string.lower():
                    print("\nScript with AJAX/API references:")
                    print(script.string[:500])

    else:
        print(f"Error: Got status code {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
