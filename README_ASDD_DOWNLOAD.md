# ASDD Data Downloader for West Bengal CEO Website

This tool downloads ASDD (Absent/Shifted/Deceased) voter list data from the West Bengal Chief Electoral Officer website (https://ceowestbengal.wb.gov.in/asd_sir).

## ⚠️ IMPORTANT: CAPTCHA Limitation

**The website requires CAPTCHA verification for downloads, which means fully automated downloading is not possible.**

### Available Solutions:

1. **Semi-Automated (RECOMMENDED)**: Use `download_asdd_manual.py`
   - Script clicks download buttons automatically
   - You solve CAPTCHAs manually when they appear
   - Best balance between automation and CAPTCHA requirements

2. **URL Extraction**: Use `extract_asdd_urls.py`
   - Extracts download information without clicking
   - Saves data to CSV for review
   - No downloads, just information gathering

3. **Fully Manual**: Use the website normally

## Overview

The ASDD list contains voters whose names were in the West Bengal Electoral Rolls but are not included in the Draft Roll. Due to CAPTCHA protection, this tool provides semi-automated assistance rather than fully automated downloading.

## Prerequisites

### 1. Python Installation
- Python 3.8 or higher
- Check your Python version: `python3 --version` or `python --version`

### 2. Chrome Browser
- Google Chrome must be installed on your computer
- Download from: https://www.google.com/chrome/

### 3. ChromeDriver
- ChromeDriver must match your Chrome version
- **Auto-install (Recommended)**:
  ```bash
  pip install webdriver-manager
  ```
- **Manual install**: Download from https://chromedriver.chromium.org/downloads

## Installation

### Step 1: Clone or Download This Repository

```bash
git clone https://github.com/chhandasbhattacharyya/AgentLaboratory.git
cd AgentLaboratory
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements_asdd.txt
```

Or install manually:
```bash
pip install selenium beautifulsoup4 requests lxml
```

### Step 3: Verify Installation

```bash
python3 download_asdd_selenium.py --help
```

## Usage

### RECOMMENDED: Semi-Automated Downloading (Handles CAPTCHA)

**Use this method to download data with manual CAPTCHA solving:**

```bash
python download_asdd_manual.py
```

**How it works:**
1. Browser opens and navigates to ASDD page
2. You have 15 seconds to manually select District and Assembly Constituency
3. Press ENTER when table loads
4. Script automatically clicks each Download button
5. **When CAPTCHA appears, solve it manually** during the 10-second wait
6. Script continues after each download
7. Files save to `asdd_data/` folder

**Interactive controls:**
- If download fails, you can: skip, retry, or stop
- Script waits 10 seconds between downloads for CAPTCHA solving
- You must stay present to solve CAPTCHAs

---

### Alternative: Extract URLs Only (No Downloads)

**Use this to gather information without triggering CAPTCHA:**

```bash
python extract_asdd_urls.py
```

This saves polling station info to CSV without downloading files.

---

### DEPRECATED: Fully Automated (Blocked by CAPTCHA)

**Note:** The following methods will fail due to CAPTCHA protection. Use semi-automated approach instead.

#### Test with a Single District (Will Trigger CAPTCHA)

To test the script with Malda district:

```bash
python3 download_asdd_selenium.py --test-district "Malda"
```

To test with any other district:

```bash
python3 download_asdd_selenium.py --test-district "Kolkata"
```

### Download All Districts

To download data for all districts:

```bash
python3 download_asdd_selenium.py
```

### Options

```bash
# Show the browser window (not headless mode)
python3 download_asdd_selenium.py --show-browser

# Specify custom output directory
python3 download_asdd_selenium.py --output-dir /path/to/save/data

# Combine options
python3 download_asdd_selenium.py --test-district "Malda" --show-browser
```

## Output Structure

Downloaded data will be organized as:

```
asdd_data/
├── download_progress.json    # Progress tracking (can resume if interrupted)
├── asdd_download.log         # Detailed log file
├── District_Name_1/
│   ├── Assembly_Constituency_1/
│   │   ├── ASDD_Part_1.pdf
│   │   ├── ASDD_Part_2.pdf
│   │   └── ...
│   └── Assembly_Constituency_2/
│       └── ...
├── District_Name_2/
│   └── ...
└── ...
```

## Features

1. **Progress Tracking**: If the download is interrupted, you can resume from where it stopped
2. **Logging**: All activities are logged to `asdd_download.log`
3. **Auto-retry**: Failed downloads are tracked in the progress file
4. **Organized Structure**: Files are automatically organized by district and constituency
5. **Test Mode**: Test with a single district before downloading everything

## Troubleshooting

### Error: "chromedriver not found"

**Solution**: Install webdriver-manager
```bash
pip install webdriver-manager
```

Then modify the script to use:
```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=options)
```

### Error: "selenium.common.exceptions.WebDriverException"

**Solution**:
- Make sure Chrome browser is installed
- Update Chrome to the latest version
- Reinstall ChromeDriver matching your Chrome version

### Downloads Not Appearing

**Solution**:
1. Run with `--show-browser` to see what's happening
2. Check the log file: `asdd_download.log`
3. Verify your internet connection
4. The website structure may have changed - inspect the page source

### Slow Downloads

This is normal. The script includes delays to:
- Wait for page elements to load
- Avoid overwhelming the server
- Ensure downloads complete

## Alternative Script

If Selenium doesn't work, try the basic requests-based script:

```bash
python3 download_asdd_data.py
```

This uses simple HTTP requests and may work if the website doesn't require JavaScript.

## Important Notes

1. **Run Locally**: This script must be run on your local computer with unrestricted internet access, not in a sandboxed/restricted environment.

2. **Website Changes**: If the script stops working, the website structure may have changed. Check:
   - Element IDs (district, ac, part dropdowns)
   - Download button selectors
   - Page navigation flow

3. **Legal Compliance**: This data is public information from a government website. Use it responsibly and in compliance with applicable laws.

4. **Data Size**: Downloading all districts will take several hours and may require significant disk space.

## Customization

### Modifying Element Selectors

If the website structure changes, you may need to update the element selectors in `download_asdd_selenium.py`:

```python
# Current selectors
district_select = Select(self.driver.find_element(By.ID, "district"))
ac_select = Select(self.driver.find_element(By.ID, "ac"))
part_select = Select(self.driver.find_element(By.ID, "part"))
```

Inspect the webpage to find the current IDs/selectors.

### Adjusting Wait Times

If your internet is slow, increase wait times:

```python
time.sleep(5)  # Instead of time.sleep(2)
```

## Support

If you encounter issues:
1. Check the log file: `asdd_download.log`
2. Run with `--show-browser` to see the browser actions
3. Verify the website is accessible: https://ceowestbengal.wb.gov.in/asd_sir
4. Open an issue on GitHub with:
   - Error message
   - Log file contents
   - Python version
   - Chrome version

## License

This tool is provided as-is for downloading public data from government websites.

## Contributing

Contributions welcome! Please submit pull requests or open issues on GitHub.

---

**Last Updated**: December 2025
**Website**: https://ceowestbengal.wb.gov.in/asd_sir
