import requests
from bs4 import BeautifulSoup
import json
import os
import logging
from urllib.parse import urlparse
from pathlib import Path
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SCRAPPED_DATA_FOLDER = "../ScrappedData"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
REQUEST_TIMEOUT = 15

# List of URLs to scrape - ADD MORE URLs HERE
WEBSITES_TO_SCRAPE = [
    "https://www.meezanbank.com/car-ijarah",
    # Add more URLs here
    # "https://example.com/page1",
    # "https://example.com/page2",
]


def create_output_folder():
    """Create ScrappedData folder if it doesn't exist"""
    Path(SCRAPPED_DATA_FOLDER).mkdir(exist_ok=True)
    logger.info(f"Output folder ready: {SCRAPPED_DATA_FOLDER}")


def init_selenium_driver():
    """Initialize Selenium WebDriver for JavaScript rendering"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logger.warning(f"Chrome not available, trying Firefox: {e}")
        try:
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            options.add_argument('-profile')
            driver = webdriver.Firefox(options=options)
            return driver
        except Exception as e:
            logger.error(f"Neither Chrome nor Firefox available: {e}")
            return None


def extract_page_title(soup, url):
    """Extract page title from og:title, title tag, or URL"""
    # Try og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()
    
    # Try regular title
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        return title_tag.string.strip()
    
    # Fallback to domain
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('www.', '').split('.')[0]
    return domain.capitalize()


def sanitize_filename(filename):
    """Make filename filesystem-safe"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip()[:100]
    return filename or "page"


def clean_text_for_embeddings(text):
    """Clean text specifically for RAG/embedding training"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove common navigation/duplicate patterns
    lines = text.split(' ')
    filtered_lines = []
    seen_phrases = set()
    
    i = 0
    while i < len(lines):
        # Create a short phrase window (3-5 words)
        phrase_window = ' '.join(lines[i:min(i+4, len(lines))])
        
        # Skip duplicate navigation items
        if phrase_window not in seen_phrases:
            filtered_lines.append(lines[i])
            seen_phrases.add(phrase_window)
        
        i += 1
    
    text = ' '.join(filtered_lines)
    
    # Remove common boilerplate
    boilerplate_patterns = [
        r'.*?Close Menu.*?x x اردو.*?',
        r'.*?Connect with us.*?Share.*?',
        r'.*?Login Register.*?',
        r'.*?Select.*?Select.*?',
        r'facebook linkedin whatsapp email print',
        r'©.*?all rights reserved',
    ]
    
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # Remove repeated words (like "Bank Accounts Bank Accounts")
    text = re.sub(r'\b(\w+)\s+(?=\1\b)', '', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces again
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_content_sections(soup):
    """Extract main content sections separately for better structure"""
    sections = {}
    
    # Try to extract main content area (usually in main or article tags)
    main_content = soup.find(['main', 'article', 'section'])
    if main_content:
        # Extract headings and their related content
        current_section = "introduction"
        buffer = []
        
        for element in main_content.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'li']):
            if element.name in ['h1', 'h2', 'h3']:
                # Save previous section
                if buffer:
                    sections[current_section] = ' '.join(buffer).strip()
                    buffer = []
                # Start new section
                current_section = element.get_text().strip()[:100]
            else:
                text = element.get_text().strip()
                if text:
                    buffer.append(text)
        
        # Save last section
        if buffer:
            sections[current_section] = ' '.join(buffer).strip()
    
    return sections if sections else {}


def extract_all_text(html_content):
    """Extract all text from HTML with aggressive cleaning for RAG"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove unwanted elements completely
    unwanted_tags = soup(["script", "style", "meta", "noscript", "nav", "footer", 
                         "form", "button", "input", ".sidebar", ".menu", ".navbar"])
    for element in unwanted_tags:
        element.decompose()
    
    # Extract structured sections
    sections = extract_content_sections(soup)
    
    if sections:
        # Use structured content
        full_text = " ".join([f"{section}: {content}" for section, content in sections.items()])
    else:
        # Fallback to full text extraction
        full_text = soup.get_text(separator=" ")
    
    # Clean the extracted text
    full_text = clean_text_for_embeddings(full_text)
    
    return full_text


def scrape_with_selenium(url):
    """Scrape JavaScript-rendered content using Selenium"""
    driver = init_selenium_driver()
    
    if not driver:
        logger.warning(f"No browser available, falling back to requests for {url}")
        return scrape_with_requests(url)
    
    try:
        logger.info(f"[Selenium] Loading: {url}")
        driver.get(url)
        
        # Wait for dynamic content to load (max 10 seconds)
        try:
            WebDriverWait(driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except:
            pass
        
        # Additional wait for JavaScript rendering
        time.sleep(3)
        
        # Get page source after JavaScript execution
        page_source = driver.page_source
        
        # Extract title and metadata
        soup = BeautifulSoup(page_source, "html.parser")
        page_title = extract_page_title(soup, url)
        
        # Extract all text
        page_text = extract_all_text(page_source)
        
        # Get description
        description = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
        
        logger.info(f"✓ Extracted {len(page_text)} characters from {page_title}")
        
        # Create chunks for RAG training
        chunks = chunk_text(page_text, chunk_size=500, overlap=50)
        
        return {
            "metadata": {
                "url": url,
                "title": page_title,
                "description": description,
                "scraped_at": datetime.now().isoformat(),
                "status": "success",
                "method": "selenium",
                "content_length": len(page_text),
                "word_count": len(page_text.split()),
                "chunk_count": len(chunks),
                "suitable_for_rag": True
            },
            "content": page_text,
            "chunks": chunks
        }, page_title
        
    except Exception as e:
        logger.error(f"✗ Selenium error for {url}: {e}")
        return None, None
    finally:
        try:
            driver.quit()
        except:
            pass


def scrape_with_requests(url):
    """Fallback: Scrape with basic requests"""
    try:
        logger.info(f"[Requests] Loading: {url}")
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        page_title = extract_page_title(soup, url)
        page_text = extract_all_text(response.text)
        
        description = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
        
        logger.info(f"✓ Extracted {len(page_text)} characters from {page_title}")
        
        # Create chunks for RAG training
        chunks = chunk_text(page_text, chunk_size=500, overlap=50)
        
        return {
            "metadata": {
                "url": url,
                "title": page_title,
                "description": description,
                "scraped_at": datetime.now().isoformat(),
                "status": "success",
                "method": "requests",
                "content_length": len(page_text),
                "word_count": len(page_text.split()),
                "chunk_count": len(chunks),
                "suitable_for_rag": True
            },
            "content": page_text,
            "chunks": chunks
        }, page_title
        
    except Exception as e:
        logger.error(f"✗ Requests error for {url}: {e}")
        return None, None


def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into chunks for RAG training
    chunk_size: approximate words per chunk
    overlap: words to overlap between chunks
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def scrape_website(url):
    """Scrape website with Selenium first, fallback to requests"""
    data, title = scrape_with_selenium(url)
    return data, title


def save_to_json(data, filename):
    """Save scraped data to JSON file"""
    try:
        safe_filename = sanitize_filename(filename)
        filepath = os.path.join(SCRAPPED_DATA_FOLDER, f"{safe_filename}.json")
        
        # If file exists, rename it
        counter = 1
        base_path = filepath
        while os.path.exists(filepath):
            safe_filename_new = f"{sanitize_filename(filename)} ({counter})"
            filepath = os.path.join(SCRAPPED_DATA_FOLDER, f"{safe_filename_new}.json")
            counter += 1
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ Saved to: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error saving file: {e}")
        return False


def scrape_all_websites():
    """Main function to scrape all websites"""
    logger.info("=" * 70)
    logger.info("Starting Web Scraping Process...")
    logger.info("=" * 70)
    
    create_output_folder()
    
    if not WEBSITES_TO_SCRAPE:
        logger.warning("No websites to scrape. Add URLs to WEBSITES_TO_SCRAPE list.")
        return
    
    successful = 0
    failed = 0
    
    for url in WEBSITES_TO_SCRAPE:
        data, page_title = scrape_website(url)
        
        if data:
            if save_to_json(data, page_title):
                successful += 1
                logger.info(f"   Content: {data['metadata']['content_length']} chars | Words: {data['metadata']['word_count']} | Chunks: {data['metadata']['chunk_count']}")
            else:
                failed += 1
        else:
            failed += 1
    
    # Summary
    logger.info("=" * 70)
    logger.info(f"Scraping Complete!")
    logger.info(f"Successful: {successful} | Failed: {failed}")
    logger.info(f"Output folder: {os.path.abspath(SCRAPPED_DATA_FOLDER)}")
    logger.info("=" * 70)


if __name__ == "__main__":
    scrape_all_websites()