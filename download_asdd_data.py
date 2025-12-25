#!/usr/bin/env python3
"""
Script to download ASDD (Absent/Shifted/Deceased) voter list data from CEO West Bengal website.
Downloads data district by district, assembly constituency by constituency, and part by part.
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import json
from pathlib import Path
from urllib.parse import urljoin
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ASDDDownloader:
    def __init__(self, base_url="https://ceowestbengal.wb.gov.in", output_dir="asdd_data"):
        self.base_url = base_url
        self.asd_url = f"{base_url}/asd_sir"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Setup session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })

        self.stats = {
            'districts': 0,
            'constituencies': 0,
            'parts': 0,
            'downloaded': 0,
            'failed': 0
        }

    def get_page(self, url, max_retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def get_districts(self):
        """Extract list of districts from the main page"""
        logger.info("Fetching districts list...")
        try:
            response = self.get_page(self.asd_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for district dropdown/select element
            district_select = soup.find('select', {'id': 'district'}) or \
                            soup.find('select', {'name': 'district'}) or \
                            soup.find('select', class_=lambda x: x and 'district' in x.lower())

            if district_select:
                districts = []
                for option in district_select.find_all('option'):
                    value = option.get('value', '').strip()
                    text = option.get_text().strip()
                    if value and value != '0' and text.lower() != 'select':
                        districts.append({'value': value, 'name': text})
                logger.info(f"Found {len(districts)} districts")
                return districts
            else:
                logger.error("Could not find district dropdown on page")
                return []
        except Exception as e:
            logger.error(f"Error fetching districts: {e}")
            return []

    def get_constituencies(self, district_code):
        """Get assembly constituencies for a district"""
        logger.info(f"Fetching constituencies for district {district_code}...")
        try:
            # The website likely has an AJAX endpoint for this
            # We'll need to inspect the network requests
            # Common patterns: /api/getConstituencies or similar

            # Try common endpoints
            endpoints = [
                f"{self.base_url}/api/getAC",
                f"{self.base_url}/api/getConstituencies",
                f"{self.base_url}/getAC.php",
                f"{self.base_url}/getConstituency.php",
            ]

            for endpoint in endpoints:
                try:
                    response = self.session.post(
                        endpoint,
                        data={'district': district_code},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            return data
                except:
                    continue

            return []
        except Exception as e:
            logger.error(f"Error fetching constituencies: {e}")
            return []

    def get_parts(self, district_code, ac_code):
        """Get part numbers for an assembly constituency"""
        logger.info(f"Fetching parts for AC {ac_code}...")
        try:
            # Similar to constituencies, likely an AJAX call
            endpoints = [
                f"{self.base_url}/api/getParts",
                f"{self.base_url}/api/getPartNo",
                f"{self.base_url}/getPart.php",
            ]

            for endpoint in endpoints:
                try:
                    response = self.session.post(
                        endpoint,
                        data={'district': district_code, 'ac': ac_code},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            return data
                except:
                    continue

            return []
        except Exception as e:
            logger.error(f"Error fetching parts: {e}")
            return []

    def download_file(self, url, output_path):
        """Download a file to the specified path"""
        try:
            response = self.get_page(url)

            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False

    def download_all(self):
        """Download all ASDD data for all districts"""
        logger.info("Starting download process...")

        districts = self.get_districts()
        if not districts:
            logger.error("No districts found. The website structure may have changed.")
            logger.info("Attempting alternative scraping method...")
            self.scrape_direct_links()
            return

        self.stats['districts'] = len(districts)

        for district in districts:
            district_name = district['name']
            district_code = district['value']

            logger.info(f"\n{'='*60}")
            logger.info(f"Processing District: {district_name} ({district_code})")
            logger.info(f"{'='*60}")

            # Create district folder
            district_dir = self.output_dir / self.sanitize_filename(district_name)
            district_dir.mkdir(exist_ok=True)

            # Get constituencies
            constituencies = self.get_constituencies(district_code)
            self.stats['constituencies'] += len(constituencies)

            for ac in constituencies:
                ac_name = ac.get('name', ac.get('text', 'Unknown'))
                ac_code = ac.get('value', ac.get('code', ''))

                logger.info(f"Processing AC: {ac_name} ({ac_code})")

                # Create AC folder
                ac_dir = district_dir / self.sanitize_filename(ac_name)
                ac_dir.mkdir(exist_ok=True)

                # Get parts
                parts = self.get_parts(district_code, ac_code)
                self.stats['parts'] += len(parts)

                for part in parts:
                    part_no = part.get('part', part.get('value', ''))

                    # Construct download URL
                    # This is a guess - need to inspect actual requests
                    download_url = f"{self.base_url}/asd_download.php?district={district_code}&ac={ac_code}&part={part_no}"

                    output_file = ac_dir / f"ASDD_Part_{part_no}.pdf"

                    if self.download_file(download_url, output_file):
                        self.stats['downloaded'] += 1
                    else:
                        self.stats['failed'] += 1

                    # Be polite to the server
                    time.sleep(0.5)

        self.print_stats()

    def scrape_direct_links(self):
        """Alternative method: scrape all direct download links from the page"""
        logger.info("Using direct link scraping method...")
        try:
            response = self.get_page(self.asd_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Save the HTML for inspection
            html_file = self.output_dir / "page_source.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            logger.info(f"Saved page source to {html_file}")

            # Look for all PDF links
            links = soup.find_all('a', href=lambda x: x and ('.pdf' in x.lower() or 'download' in x.lower()))

            logger.info(f"Found {len(links)} potential download links")

            for link in links:
                href = link.get('href')
                text = link.get_text().strip()

                # Construct full URL
                if href.startswith('http'):
                    url = href
                else:
                    url = urljoin(self.asd_url, href)

                # Create filename from link text or URL
                filename = self.sanitize_filename(text if text else os.path.basename(href))
                if not filename.endswith('.pdf'):
                    filename += '.pdf'

                output_file = self.output_dir / filename

                if self.download_file(url, output_file):
                    self.stats['downloaded'] += 1
                else:
                    self.stats['failed'] += 1

                time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error in direct link scraping: {e}")

    def sanitize_filename(self, filename):
        """Clean filename for safe filesystem usage"""
        # Remove invalid characters
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
    downloader = ASDDDownloader()
    downloader.download_all()


if __name__ == "__main__":
    main()
