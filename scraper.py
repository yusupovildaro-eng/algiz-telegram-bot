"""
Scraper for armaselektronik.com/tr

Two-level structure:
  Category page  → list of product URLs
  Product page   → name (TR), description (TR), features (TR), images
"""

import hashlib
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from config import SHOP_URL, CATALOG_CATEGORIES

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
CDN = "https://cdn.armaselektronik.com"

_session = requests.Session()
_retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
_session.mount("https://", HTTPAdapter(max_retries=_retry))


def _get(url: str) -> BeautifulSoup:
    time.sleep(1)  # polite delay between requests
    resp = _session.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def _make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _is_product_link(tag) -> bool:
    """True if anchor's child img points to /uploads/product/ (not category/slider)."""
    img = tag.find("img")
    if not img:
        return False
    src = img.get("src", "") or img.get("data-src", "")
    return "/uploads/product/" in src and "/uploads/category/" not in src


def fetch_category_products(category_path: str) -> list[dict]:
    """Fetch product stubs from one sub-category page."""
    url = SHOP_URL.rstrip("/") + "/" + category_path.lstrip("/")
    try:
        soup = _get(url)
    except Exception as e:
        print(f"  [skip] {url}: {e}")
        return []

    products = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith(SHOP_URL):
            continue
        if href in seen:
            continue
        # Only include if it looks like a product (has /uploads/product/ image)
        if _is_product_link(a):
            img = a.find("img")
            img_url = img.get("src") or img.get("data-src", "") if img else ""
            products.append({
                "id": _make_id(href),
                "product_url": href,
                "name_tr": a.get("title") or a.get_text(strip=True),
                "image_url": img_url if img_url.startswith("http") else CDN + img_url,
            })
            seen.add(href)

    return products


def fetch_all_products(limit_per_category: int = 50) -> list[dict]:
    """Collect all products across all catalog categories."""
    all_products = []
    seen_ids = set()

    for cat in CATALOG_CATEGORIES:
        items = fetch_category_products(cat)
        for item in items[:limit_per_category]:
            if item["id"] not in seen_ids:
                all_products.append(item)
                seen_ids.add(item["id"])

    return all_products


def fetch_product_detail(product: dict) -> dict:
    """
    Enrich product with full Turkish description and gallery images.
    Adds keys: description_tr (str), features_tr (list[str]), gallery_images (list[str])
    """
    url = product.get("product_url", "")
    if not url:
        return product

    try:
        soup = _get(url)
    except Exception as e:
        print(f"  [detail skip] {url}: {e}")
        return product

    # --- Product name (from h1 or page title) ---
    h1 = soup.find("h1")
    if h1:
        product["name_tr"] = h1.get_text(strip=True)

    # --- Gallery images ---
    gallery = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if "/uploads/gallery/" in src:
            if src.startswith("/"):
                src = CDN + src
            gallery.append(src)
    # fallback to product thumbnail
    if not gallery and product.get("image_url"):
        gallery = [product["image_url"]]
    product["gallery_images"] = gallery[:6]

    # --- Description text (all paragraph text, skipping navigation) ---
    # Remove nav/header/footer noise
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    # Collect feature list items
    features = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if len(text) > 10:
            features.append(text)

    # Main body text from paragraphs
    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 30:
            paragraphs.append(text)

    product["features_tr"] = features[:15]
    product["description_tr"] = " ".join(paragraphs[:6])

    return product
