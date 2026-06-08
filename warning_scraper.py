"""
Scraper for warninglightbars.com/products/
WooCommerce site, English language → Claude translates to Russian.
176 products across 15 pages (/products/page/N/).
"""

import hashlib
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

BASE = "https://warninglightbars.com"
CATALOG_URL = f"{BASE}/products/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_session = requests.Session()
_retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
_session.mount("https://", HTTPAdapter(max_retries=_retry))


def _get(url: str) -> BeautifulSoup:
    time.sleep(1)
    resp = _session.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser")


def _make_id(url: str) -> str:
    return "wlb_" + hashlib.md5(url.encode()).hexdigest()[:10]


def _thumb_to_full(src: str) -> str:
    """Convert 300x300 thumbnail URL to 600x600."""
    return src.replace("-300x300.", "-600x600.")


def fetch_page_products(page: int = 1) -> list[dict]:
    url = CATALOG_URL if page == 1 else f"{CATALOG_URL}page/{page}/"
    try:
        soup = _get(url)
    except Exception as e:
        print(f"  [skip] {url}: {e}")
        return []

    products = []
    seen = set()

    for li in soup.find_all("li", class_=lambda c: c and "product" in c):
        a_img = li.find("a", href=True)
        if not a_img:
            continue
        href = a_img["href"]
        if href in seen or "/product/" not in href:
            continue

        img = li.find("img", src=True)
        img_src = _thumb_to_full(img["src"]) if img else ""

        name_el = li.find("h3") or li.find("h2")
        name = name_el.get_text(strip=True) if name_el else li.find("a", href=href).get("title", "")

        if not name:
            continue

        products.append({
            "id": _make_id(href),
            "product_url": href,
            "name_en": name,
            "image_url": img_src,
            "source": "wlb",
        })
        seen.add(href)

    return products


def fetch_all_wlb_products(max_pages: int = 15) -> list[dict]:
    all_products = []
    seen_ids = set()
    for page in range(1, max_pages + 1):
        items = fetch_page_products(page)
        if not items:
            break
        for item in items:
            if item["id"] not in seen_ids:
                all_products.append(item)
                seen_ids.add(item["id"])
    return all_products


def fetch_product_detail(product: dict) -> dict:
    url = product.get("product_url", "")
    if not url:
        return product
    try:
        soup = _get(url)
    except Exception as e:
        print(f"  [detail skip] {url}: {e}")
        return product

    # --- Product images: class contains 'woocommerce_single' ---
    gallery = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        cls = " ".join(img.get("class", []))
        if "woocommerce_single" in cls and "wp-content/uploads" in src:
            if src not in gallery:
                gallery.append(src)

    # Fallback: thumbnail with parent ciyashop-product-thumbnail__image
    if not gallery:
        for img in soup.find_all("img", src=True):
            src = img["src"]
            parent_cls = " ".join(img.parent.get("class", []) if img.parent else [])
            if "ciyashop-product-thumbnail__image" in parent_cls:
                full = _thumb_to_full(src)
                if full not in gallery:
                    gallery.append(full)

    product["gallery_images"] = gallery[:4]
    if gallery:
        product["image_url"] = gallery[0]

    # --- Description: short description block ---
    desc = ""
    for sel in [
        ".woocommerce-product-details__short-description",
        ".woocommerce-Tabs-panel--description",
        "#tab-description",
    ]:
        el = soup.select_one(sel)
        if el:
            desc = el.get_text(" ", strip=True)[:800]
            break
    product["description_en"] = desc

    # --- Specs: parse from description lines (site has no table) ---
    specs = []
    if desc:
        for line in desc.replace("–", "\n").replace("•", "\n").splitlines():
            line = line.strip().strip("-–•").strip()
            if 8 < len(line) < 160 and ":" in line or len(line) > 15:
                specs.append(line)
    product["specs_en"] = [s for s in specs if len(s) > 8][:12]

    return product
