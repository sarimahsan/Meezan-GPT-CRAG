import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, time, threading, queue

# ============================================================
# CONFIG
# ============================================================
CONFIG = {
    "base_url":    "https://www.meezanbank.com/",
    "delay":       0.3,       # seconds between requests per worker
    "timeout":     5,         # request timeout in seconds
    "max_workers": 5,         # concurrent threads
    "max_pages":   200,       # hard cap on pages to crawl (0 = unlimited)
}

# ============================================================
# ANSI COLORS
# ============================================================
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[32m"
    RED    = "\033[31m"
    YELLOW = "\033[33m"
    CYAN   = "\033[36m"
    DIM    = "\033[2m"
    WHITE  = "\033[97m"

# ============================================================
# TERMINAL UI
# ============================================================
_print_lock = threading.Lock()

def log(msg):
    with _print_lock:
        print(f"  {C.GREEN}✓{C.RESET}  {msg}")

def skip(msg):
    with _print_lock:
        print(f"  {C.YELLOW}⊘{C.RESET}  {C.DIM}{msg}{C.RESET}")

def error(msg):
    with _print_lock:
        print(f"  {C.RED}✗{C.RESET}  {C.DIM}{msg}{C.RESET}")

def info(msg):
    with _print_lock:
        print(f"  {C.CYAN}→{C.RESET}  {msg}")

def divider(char="─", width=58):
    with _print_lock:
        print(f"  {C.DIM}{char * width}{C.RESET}")

def header(title):
    with _print_lock:
        pad = (58 - len(title) - 2) // 2
        print(f"\n  {C.DIM}{'─' * pad}{C.RESET} {C.BOLD}{C.WHITE}{title}{C.RESET} {C.DIM}{'─' * pad}{C.RESET}\n")

def print_stat(label, value, color=C.WHITE):
    with _print_lock:
        print(f"  {C.DIM}{label:<22}{C.RESET} {color}{C.BOLD}{value}{C.RESET}")

# ============================================================
# HELPERS
# ============================================================
BASE = CONFIG["base_url"]
_base_netloc = urlparse(BASE).netloc

BAD_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".css", ".js", ".ico", ".zip", ".rar",
    ".doc", ".docx", ".xls", ".xlsx", ".mp4", ".webp",
}

def is_internal(url: str) -> bool:
    return urlparse(url).netloc == _base_netloc

def normalize(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path.rstrip('/')}"

def is_valid_url(url: str) -> bool:
    lower = url.lower()
    if any(lower.endswith(ext) for ext in BAD_EXTENSIONS):
        return False
    if any(seg in url for seg in ("/ur-", "/ur/", "/api/", "graphql")):
        return False
    if url.startswith(("mailto:", "tel:", "javascript:")):
        return False
    if "#" in url:
        return False
    return True

def is_valid_response(resp) -> bool:
    return (
        resp.status_code == 200
        and "text/html" in resp.headers.get("Content-Type", "")
    )

def has_content(soup) -> bool:
    return len(soup.get_text(strip=True)) > 120

# ============================================================
# CRAWLER STATE
# ============================================================
visited:  set[str]  = set()
results:  list[dict] = []
_visited_lock = threading.Lock()
_results_lock = threading.Lock()
skipped = 0
_skipped_lock = threading.Lock()

# ============================================================
# WORKER
# ============================================================
def crawl_page(url: str) -> set[str]:
    global skipped
    try:
        resp = requests.get(url, timeout=CONFIG["timeout"], headers={
            "User-Agent": "Mozilla/5.0 (compatible; SiteMapper/2.0)"
        })
        if not is_valid_response(resp):
            with _skipped_lock: skipped += 1
            skip(f"[{resp.status_code}] {url}")
            return set()

        soup = BeautifulSoup(resp.text, "html.parser")

        if not has_content(soup):
            with _skipped_lock: skipped += 1
            skip(f"[empty] {url}")
            return set()

        links = set()
        for a in soup.find_all("a", href=True):
            full = normalize(urljoin(BASE, a["href"]))
            if is_internal(full) and is_valid_url(full):
                links.add(full)

        with _results_lock:
            results.append({"url": url, "links_found": len(links)})

        log(f"{url}  {C.DIM}({len(links)} links){C.RESET}")
        return links

    except requests.exceptions.Timeout:
        with _skipped_lock: skipped += 1
        skip(f"[timeout] {url}")
        return set()
    except Exception as exc:
        with _skipped_lock: skipped += 1
        error(f"{url} → {exc}")
        return set()

# ============================================================
# BFS ORCHESTRATOR
# ============================================================
def run_crawler():
    page_queue: queue.Queue[str] = queue.Queue()
    page_queue.put(normalize(BASE))
    visited.add(normalize(BASE))

    max_p = CONFIG["max_pages"]

    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
        futures = {}

        def submit_next():
            while not page_queue.empty():
                if max_p and len(visited) >= max_p:
                    break
                url = page_queue.get_nowait()
                fut = executor.submit(crawl_page, url)
                futures[fut] = url

        submit_next()

        while futures:
            done_futures = list(as_completed(futures))
            for fut in done_futures:
                del futures[fut]
                new_links = fut.result()
                time.sleep(CONFIG["delay"])

                for link in new_links:
                    with _visited_lock:
                        if link not in visited:
                            if max_p and len(visited) >= max_p:
                                break
                            visited.add(link)
                            page_queue.put(link)

                submit_next()

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    header("WEB CRAWLER  v2.0")
    info(f"Base URL   : {C.CYAN}{BASE}{C.RESET}")
    info(f"Workers    : {CONFIG['max_workers']}")
    info(f"Delay      : {CONFIG['delay']}s")
    info(f"Max pages  : {CONFIG['max_pages'] or 'unlimited'}")
    divider()

    start = time.time()
    run_crawler()
    elapsed = round(time.time() - start, 2)

    # ── Save output ──────────────────────────────────────────
    valid_links = [r["url"] for r in results]
    output = {
        "base_url":          BASE,
        "total_valid_pages": len(valid_links),
        "skipped_pages":     skipped,
        "crawl_time_sec":    elapsed,
        "links":             valid_links,
        "details":           results,
    }
    with open("clean_links.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    # ── Final report ─────────────────────────────────────────
    header("CRAWL COMPLETE")
    print_stat("Valid pages",   len(valid_links),  C.GREEN)
    print_stat("Skipped pages", skipped,            C.YELLOW)
    print_stat("Time elapsed",  f"{elapsed}s",      C.CYAN)
    print_stat("Output file",   "clean_links.json", C.WHITE)
    divider()
    print()