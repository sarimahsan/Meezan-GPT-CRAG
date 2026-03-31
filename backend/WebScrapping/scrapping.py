import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
except Exception:
    webdriver = None
    WebDriverWait = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 20

WEBSITES_TO_SCRAPE = [
    "https://www.meezanbank.com/awards-and-recognition",
    "https://www.meezanbank.com/home-remittance",
    "https://www.meezanbank.com/iiib",
    "https://www.meezanbank.com/Policies",
    "https://www.meezanbank.com/car-ijarah",
    "https://www.meezanbank.com/financial-information",
    "https://www.meezanbank.com/cash-management",
    "https://www.meezanbank.com/careers",
    "https://www.meezanbank.com/historical-profit-rates",
    "https://www.meezanbank.com/rupee-current-account",
    "https://www.meezanbank.com/placement-of-financial-statements-for-the-year-ended-december-31-2025",
    "https://www.meezanbank.com/export-financing",
    "https://www.meezanbank.com/women-account",
    "https://www.meezanbank.com/treasury",
    "https://www.meezanbank.com/easy-home",
    "https://www.meezanbank.com/corporate-banking",
    "https://www.meezanbank.com/investor-relations/financial-information",
    "https://www.meezanbank.com/ways-to-bank",
    "https://www.meezanbank.com/Deposit-Protection-Mechanism",
    "https://www.meezanbank.com/commercial-vehicles",
    "https://www.meezanbank.com/iban-generator",
    "https://www.meezanbank.com/premium-banking",
    "https://www.meezanbank.com/commercial-banking",
    "https://www.meezanbank.com/freedom-bank-network-expansion",
    "https://www.meezanbank.com/about-us",
    "https://www.meezanbank.com/business-bank-accounts",
    "https://www.meezanbank.com/card-discounts",
    "https://www.meezanbank.com/financial-institutions",
    "https://www.meezanbank.com/calculators",
    "https://www.meezanbank.com/media-centre",
    "https://www.meezanbank.com/eipo",
    "https://www.meezanbank.com/shariah-advisory-services",
    "https://www.meezanbank.com/Disclaimer",
    "https://www.meezanbank.com/glossary-of-terms",
    "https://www.meezanbank.com/agricultural-finance",
    "https://www.meezanbank.com/contact-us",
    "https://www.meezanbank.com/meezan-kafalah",
    "https://www.meezanbank.com/digital-bank-accounts",
    "https://www.meezanbank.com/investment-banking",
    "https://www.meezanbank.com/info-for-investors",
    "https://www.meezanbank.com/kazakhstan-bilateral-trade-mou",
    "https://www.meezanbank.com/investor-relations/info-for-investors",
    "https://www.meezanbank.com/csr",
    "https://www.meezanbank.com/consumer-financial-protection-framework",
    "https://www.meezanbank.com/investor-relations-contact-us",
    "https://www.meezanbank.com/freelancer-accounts",
    "https://www.meezanbank.com/branch-locator",
    "https://www.meezanbank.com/sitemap",
    "https://www.meezanbank.com/term-certificates",
    "https://www.meezanbank.com/publications",
    "https://www.meezanbank.com/best-bank-of-pakistan-2023",
    "https://www.meezanbank.com/Governance",
    "https://www.meezanbank.com/senior-citizen-account",
    "https://www.meezanbank.com/sohni-dharti-remittance-account",
    "https://www.meezanbank.com/plus-account",
    "https://www.meezanbank.com/dollar-current-account",
    "https://www.meezanbank.com/express-current-account",
    "https://www.meezanbank.com/euro-current-account",
    "https://www.meezanbank.com/rupee-savings-account",
    "https://www.meezanbank.com/pound-current-account",
    "https://www.meezanbank.com/smart-wallet-current",
    "https://www.meezanbank.com/euro-savings-account",
    "https://www.meezanbank.com/bachat-account",
    "https://www.meezanbank.com/dollar-savings-account",
    "https://www.meezanbank.com/teens-club-account",
    "https://www.meezanbank.com/smart-wallet-savings",
    "https://www.meezanbank.com/kids-club-account",
    "https://www.meezanbank.com/smart-remittance-wallet",
    "https://www.meezanbank.com/asaan-current-account",
    "https://www.meezanbank.com/labbaik-account",
    "https://www.meezanbank.com/asaan-remittance-account",
    "https://www.meezanbank.com/express-savings-account",
    "https://www.meezanbank.com/roshan-resident-account",
    "https://www.meezanbank.com/pound-savings-account",
    "https://www.meezanbank.com/asaan-savings-account",
    "https://www.meezanbank.com/asaan-mobile-account",
    "https://www.meezanbank.com/smart-disbursement-solution",
    "https://www.meezanbank.com/roshan-samaji-khidmat",
    "https://www.meezanbank.com/naya-pakistan-certificate",
    "https://www.meezanbank.com/govt-hajj-2026",
    "https://www.meezanbank.com/roshan-pension-plan",
    "https://www.meezanbank.com/invest-in-psx",
    "https://www.meezanbank.com/roshan-apna-ghar",
    "https://www.meezanbank.com/regulatory-announcements",
    "https://www.meezanbank.com/iiib-certificates",
    "https://www.meezanbank.com/analyst-presentation",
    "https://www.meezanbank.com/unclaimed",
    "https://www.meezanbank.com/apni-bike",
    "https://www.meezanbank.com/consumer-ease",
    "https://www.meezanbank.com/solar-panel-financing",
    "https://www.meezanbank.com/meezan-ebiz-plus-lite",
    "https://www.meezanbank.com/payroll-partner",
    "https://www.meezanbank.com/corporate-payroll-card",
    "https://www.meezanbank.com/why-meezan",
    "https://www.meezanbank.com/business-term-certificates",
    "https://www.meezanbank.com/life-at-meezan",
    "https://www.meezanbank.com/meezan-ebiz-plus",
    "https://www.meezanbank.com/visa-debit-card",
    "https://www.meezanbank.com/meezan-women-first",
    "https://www.meezanbank.com/apna-ghar-program",
    "https://www.meezanbank.com/meezan-women-entrepreneurs",
    "https://www.meezanbank.com/titanium-debit-card",
    "https://www.meezanbank.com/payment",
    "https://www.meezanbank.com/paypak-debit-card",
    "https://www.meezanbank.com/world-debit-card",
    "https://www.meezanbank.com/fcy-debit-card",
    "https://www.meezanbank.com/visa-infinite-debit-card",
    "https://www.meezanbank.com/organizational-chart",
    "https://www.meezanbank.com/roshan-digital-business-account",
    "https://www.meezanbank.com/karobari-munafa-account",
    "https://www.meezanbank.com/islamic-institutions-account",
    "https://www.meezanbank.com/easy-home-calculator",
    "https://www.meezanbank.com/apni-bike-calculator",
    "https://www.meezanbank.com/solar-panel-calculator",
]

BOILERPLATE_PATTERNS = [
    re.compile(r".*?Close Menu.*?x x اردو.*?", re.IGNORECASE),
    re.compile(r".*?Connect with us.*?Share.*?", re.IGNORECASE),
    re.compile(r".*?Login Register.*?", re.IGNORECASE),
    re.compile(r".*?Select.*?Select.*?", re.IGNORECASE),
    re.compile(r"facebook linkedin whatsapp email print", re.IGNORECASE),
    re.compile(r"©.*?all rights reserved", re.IGNORECASE),
]

SESSION_LOCAL = threading.local()


def is_colab() -> bool:
    return os.path.exists("/content") and ("COLAB_GPU" in os.environ or "COLAB_RELEASE_TAG" in os.environ)


def default_output_dir() -> Path:
    if is_colab():
        return Path("/content/ScrappedData")
    return Path("../ScrappedData")


def create_output_folder(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output folder ready: %s", output_dir)


def build_requests_session(pool_size: int) -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=max(32, pool_size),
        pool_maxsize=max(32, pool_size),
        max_retries=2,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session


def get_thread_session(pool_size: int) -> requests.Session:
    if not hasattr(SESSION_LOCAL, "session"):
        SESSION_LOCAL.session = build_requests_session(pool_size)
    return SESSION_LOCAL.session


def init_selenium_driver() -> Optional[webdriver.Remote]:
    if webdriver is None:
        return None

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        return webdriver.Chrome(options=options)
    except Exception as exc:
        logger.warning("Chrome not available in runtime: %s", exc)
        return None


def extract_page_title(soup: BeautifulSoup, url: str) -> str:
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        return title_tag.string.strip()

    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace("www.", "").split(".")[0]
    return domain.capitalize() or "page"


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r"[<>:\"/\\|?*]", "", filename)
    filename = filename.strip()[:100]
    return filename or "page"


def clean_text_for_embeddings(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split(" ")
    filtered: List[str] = []
    seen_phrases = set()

    for i, word in enumerate(words):
        phrase_window = " ".join(words[i : min(i + 4, len(words))])
        if phrase_window not in seen_phrases:
            filtered.append(word)
            seen_phrases.add(phrase_window)

    text = " ".join(filtered)

    for pattern in BOILERPLATE_PATTERNS:
        text = pattern.sub(" ", text)

    text = re.sub(r"\b(\w+)\s+(?=\1\b)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_content_sections(soup: BeautifulSoup) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    main_content = soup.find(["main", "article", "section"])
    if not main_content:
        return sections

    current_section = "introduction"
    buffer: List[str] = []

    for element in main_content.find_all(["h1", "h2", "h3", "p", "ul", "li"]):
        if element.name in ["h1", "h2", "h3"]:
            if buffer:
                sections[current_section] = " ".join(buffer).strip()
                buffer = []
            current_section = element.get_text().strip()[:100]
        else:
            content = element.get_text().strip()
            if content:
                buffer.append(content)

    if buffer:
        sections[current_section] = " ".join(buffer).strip()

    return sections


def extract_all_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup(["script", "style", "meta", "noscript", "nav", "footer", "form", "button", "input"]):
        tag.decompose()

    for css in [".sidebar", ".menu", ".navbar", "header"]:
        for node in soup.select(css):
            node.decompose()

    sections = extract_content_sections(soup)
    if sections:
        full_text = " ".join([f"{section}: {content}" for section, content in sections.items()])
    else:
        full_text = soup.get_text(separator=" ")

    return clean_text_for_embeddings(full_text)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks: List[str] = []
    stride = max(1, chunk_size - overlap)

    for i in range(0, len(words), stride):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


def build_document(url: str, html: str, method: str) -> Tuple[Dict, str]:
    soup = BeautifulSoup(html, "html.parser")
    page_title = extract_page_title(soup, url)
    page_text = extract_all_text(html)

    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc.get("content", "").strip() if meta_desc else ""

    chunks = chunk_text(page_text, chunk_size=500, overlap=50)

    data = {
        "metadata": {
            "url": url,
            "title": page_title,
            "description": description,
            "scraped_at": datetime.now().isoformat(),
            "status": "success",
            "method": method,
            "content_length": len(page_text),
            "word_count": len(page_text.split()),
            "chunk_count": len(chunks),
            "suitable_for_rag": True,
        },
        "content": page_text,
        "chunks": chunks,
    }
    return data, page_title


def scrape_with_requests(url: str, timeout: int, pool_size: int) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        session = get_thread_session(pool_size)
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return build_document(url, response.text, method="requests")
    except Exception as exc:
        logger.error("Requests error for %s: %s", url, exc)
        return None, None


def scrape_with_selenium(url: str, wait_seconds: float = 1.5) -> Tuple[Optional[Dict], Optional[str]]:
    driver = init_selenium_driver()
    if not driver:
        logger.warning("Selenium not available for %s", url)
        return None, None

    try:
        driver.get(url)
        if WebDriverWait is not None:
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except Exception:
                pass
        time.sleep(wait_seconds)
        return build_document(url, driver.page_source, method="selenium")
    except Exception as exc:
        logger.error("Selenium error for %s: %s", url, exc)
        return None, None
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def scrape_website(url: str, mode: str, timeout: int, pool_size: int, wait_seconds: float) -> Tuple[Optional[Dict], Optional[str]]:
    if mode == "requests":
        return scrape_with_requests(url, timeout=timeout, pool_size=pool_size)
    if mode == "selenium":
        return scrape_with_selenium(url, wait_seconds=wait_seconds)

    data, title = scrape_with_requests(url, timeout=timeout, pool_size=pool_size)
    if data and data.get("metadata", {}).get("word_count", 0) >= 50:
        return data, title
    return scrape_with_selenium(url, wait_seconds=wait_seconds)


def save_to_json(data: Dict, filename: str, output_dir: Path, url: str) -> bool:
    try:
        safe_filename = sanitize_filename(filename)
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
        filepath = output_dir / f"{safe_filename}_{url_hash}.json"

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True
    except Exception as exc:
        logger.error("Error saving file for %s: %s", url, exc)
        return False


def save_run_report(output_dir: Path, report: Dict) -> None:
    report_file = output_dir / "scrape_run_report.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")


def scrape_all_websites(mode: str, workers: int, timeout: int, max_urls: int, output_dir: Path, wait_seconds: float) -> None:
    start = time.time()
    create_output_folder(output_dir)

    urls = WEBSITES_TO_SCRAPE[:max_urls] if max_urls > 0 else WEBSITES_TO_SCRAPE

    if not urls:
        logger.warning("No websites to scrape.")
        return

    logger.info("=" * 70)
    logger.info("Starting scraping: mode=%s workers=%d urls=%d", mode, workers, len(urls))
    logger.info("Output folder: %s", output_dir.resolve())
    logger.info("=" * 70)

    successful = 0
    failed = 0
    total_words = 0
    total_chars = 0
    failed_urls: List[str] = []

    if mode == "selenium":
        for url in urls:
            data, page_title = scrape_website(url, mode=mode, timeout=timeout, pool_size=workers, wait_seconds=wait_seconds)
            if data and save_to_json(data, page_title or "page", output_dir, url):
                successful += 1
                meta = data["metadata"]
                total_words += meta["word_count"]
                total_chars += meta["content_length"]
            else:
                failed += 1
                failed_urls.append(url)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(scrape_website, url, mode, timeout, workers, wait_seconds): url
                for url in urls
            }

            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                try:
                    data, page_title = future.result()
                    if data and save_to_json(data, page_title or "page", output_dir, url):
                        successful += 1
                        meta = data["metadata"]
                        total_words += meta["word_count"]
                        total_chars += meta["content_length"]
                    else:
                        failed += 1
                        failed_urls.append(url)
                except Exception as exc:
                    failed += 1
                    failed_urls.append(url)
                    logger.error("Worker failed for %s: %s", url, exc)

    elapsed = max(1e-8, time.time() - start)

    report = {
        "started_at": datetime.fromtimestamp(start).isoformat(),
        "finished_at": datetime.now().isoformat(),
        "duration_seconds": elapsed,
        "mode": mode,
        "workers": workers,
        "timeout": timeout,
        "total_urls": len(urls),
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / len(urls)) * 100.0,
        "total_words": total_words,
        "total_characters": total_chars,
        "throughput_urls_per_sec": len(urls) / elapsed,
        "output_dir": str(output_dir.resolve()),
        "failed_urls": failed_urls,
        "notes": [
            "GPU VRAM is not used for scraping; throughput mainly depends on network + CPU parsing.",
            "For Colab speed, use requests mode with higher workers (16-48) depending on site limits.",
        ],
    }

    save_run_report(output_dir, report)

    logger.info("=" * 70)
    logger.info("Scraping complete | success=%d failed=%d", successful, failed)
    logger.info("Elapsed: %.2fs | Throughput: %.2f urls/s", elapsed, len(urls) / elapsed)
    logger.info("Run report: %s", (output_dir / "scrape_run_report.json").resolve())
    logger.info("=" * 70)


def parse_args() -> argparse.Namespace:
    cpu = os.cpu_count() or 8
    parser = argparse.ArgumentParser(description="Fast Colab-friendly scraper for RAG data")
    parser.add_argument("--mode", choices=["requests", "selenium", "auto"], default="requests")
    parser.add_argument("--workers", type=int, default=min(48, max(8, cpu * 4)))
    parser.add_argument("--timeout", type=int, default=REQUEST_TIMEOUT)
    parser.add_argument("--max-urls", type=int, default=0, help="0 means all URLs")
    parser.add_argument("--output-dir", type=Path, default=default_output_dir())
    parser.add_argument("--selenium-wait", type=float, default=1.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scrape_all_websites(
        mode=args.mode,
        workers=max(1, args.workers),
        timeout=max(5, args.timeout),
        max_urls=max(0, args.max_urls),
        output_dir=args.output_dir,
        wait_seconds=max(0.0, args.selenium_wait),
    )


if __name__ == "__main__":
    main()
