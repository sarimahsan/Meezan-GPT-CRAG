# Web Scraping Guide

## Configuration

Edit the `WEBSITES_TO_SCRAPE` list in `scrapping.py` to add websites you want to scrape:

```python
WEBSITES_TO_SCRAPE = [
    "https://www.meezanbank.com/car-ijarah",
    "https://example.com/page1",
    "https://example.com/page2",
]
```

## Output

Each scraped website is saved as a separate JSON file in the `ScrappedData/` folder:

```
ScrappedData/
├── Meezanbank.json
├── PageTitle1.json
└── PageTitle2.json
```

### JSON Structure

Each file contains:

```json
{
  "metadata": {
    "url": "https://website.com",
    "title": "Page Title",
    "description": "Meta description",
    "scraped_at": "2026-03-30T22:00:00.123456",
    "status": "success",
    "content_length": 5000
  },
  "content": "Extracted page content..."
}
```

## Usage

### Activate Virtual Environment

```bash
source venv/bin/activate
```

### Install Dependencies (if not already installed)

```bash
pip install requests beautifulsoup4
```

### Run the Scraper

```bash
python scrapping.py
```

### Output Example

```
2026-03-30 22:00:00 - INFO - ============================================================
2026-03-30 22:00:00 - INFO - Starting web scraping process...
2026-03-30 22:00:00 - INFO - ============================================================
2026-03-30 22:00:00 - INFO - Output folder ready: ScrappedData
2026-03-30 22:00:00 - INFO - Scraping: https://www.meezanbank.com/car-ijarah
2026-03-30 22:00:00 - INFO - ✓ Successfully scraped: Meezanbank
2026-03-30 22:00:00 - INFO - ✓ Saved to: ScrappedData/Meezanbank.json
2026-03-30 22:00:00 - INFO - ============================================================
2026-03-30 22:00:00 - INFO - Scraping Complete!
2026-03-30 22:00:00 - INFO - Successful: 1 | Failed: 0
2026-03-30 22:00:00 - INFO - Output folder: /path/to/ScrappedData
```

## Features

- ✅ Automatic filename generation from page title
- ✅ Metadata extraction (title, description, URL, timestamp)
- ✅ Clean, organized output in ScrappedData folder
- ✅ Professional logging and error handling
- ✅ Prevents invalid filenames automatically
- ✅ Extracts content from og:title meta tag
- ✅ Removes scripts and styles from content
- ✅ Timeout protection (10 seconds per request)
- ✅ User-Agent header for better compatibility

## Customization

### Change Request Timeout

In `scrapping.py`:
```python
REQUEST_TIMEOUT = 10  # seconds
```

### Change Content Limit

```python
"content": page_text[:5000]  # Limit to 5000 characters
```

### Add Custom Headers

```python
HEADERS = {
    'User-Agent': 'Your custom user agent',
}
```
