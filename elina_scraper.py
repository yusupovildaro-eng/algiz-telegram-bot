"""
Scraper for elina.ru/catalog/

List page:   <li class="catalog__item"><a class="catalog__link" href="...">Name</a></li>
Detail page: .product__price, .productInformation, img in .product__slider-preview
"""

import hashlib
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

BASE = "https://www.elina.ru"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

# Restricted to: балки СГУ, сирены (VIP-сигналы/крякалки), световые панели
CATEGORIES = [
    "/catalog/Balki_SGU/",
    "/catalog/VIP-signalyi_kryakalki/",
    "/catalog/svetovyie_paneli/",
]

_session = requests.Session()
_retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
_session.mount("https://", HTTPAdapter(max_retries=_retry))


def _get(url: str) -> BeautifulSoup:
    time.sleep(1)
    resp = _session.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser")


def _make_id(url: str) -> str:
    return "elina_" + hashlib.md5(url.encode()).hexdigest()[:10]


def fetch_category_products(category_path: str) -> list[dict]:
    url = BASE + category_path
    try:
        soup = _get(url)
    except Exception as e:
        print(f"  [skip] {url}: {e}")
        return []

    products = []
    seen = set()

    # The "catalog__link" class is used for the site-wide sidebar nav (same
    # links appear on every category page), so scope to hrefs that actually
    # belong to the requested category.
    for a in soup.find_all("a", class_="catalog__link", href=True):
        href = a["href"]
        if not href.startswith(category_path):
            continue
        if href in seen:
            continue
        name = a.get_text(strip=True)
        if not name:
            continue
        full_url = BASE + href
        products.append({
            "id": _make_id(full_url),
            "product_url": full_url,
            "name_ru": name,
            "price": "",
            "image_url": "",
            "source": "elina",
        })
        seen.add(href)

    return products


def fetch_all_elina_products(limit_per_category: int = 30) -> list[dict]:
    all_products = []
    seen_ids = set()
    for cat in CATEGORIES:
        items = fetch_category_products(cat)
        for item in items[:limit_per_category]:
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

    # --- Price ---
    price_el = soup.find(class_="product__price")
    if price_el:
        product["price"] = price_el.get_text(strip=True)

    # --- Product images ---
    # Main image: img-responsive inside .imgcurr, or any /images/product/ img
    SKIP_SRCS = ("/img/video.png", "/img/logo", "/images/slider/",
                 "/images/about/", "/themes/", "/upload/images/icons/", "/img/lozung")
    gallery = []

    # Priority 1: main displayed image inside .imgcurr
    imgcurr = soup.find(class_="imgcurr")
    if imgcurr:
        img = imgcurr.find("img", src=True)
        if img and not any(s in img["src"] for s in SKIP_SRCS):
            src = img["src"]
            gallery.append(BASE + src if src.startswith("/") else src)

    # Priority 2: any /images/product/ or /images/proj/ images
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(s in src for s in SKIP_SRCS):
            continue
        if "/images/product/" in src or "/images/proj/" in src:
            full = BASE + src if src.startswith("/") else src
            if full not in gallery:
                gallery.append(full)

    product["gallery_images"] = gallery[:6]
    if gallery:
        product["image_url"] = gallery[0]

    # --- Description and specs from .productInformation blocks ---
    descriptions = []
    for div in soup.find_all(class_="productInformation"):
        text = div.get_text(" ", strip=True)
        if len(text) > 30:
            descriptions.append(text[:400])

    product["description_ru"] = " ".join(descriptions[:2])

    # Technical specs: look for size/weight/spec data
    specs = []
    for div in soup.find_all(class_="productInformation"):
        for li in div.find_all("li"):
            text = li.get_text(strip=True)
            if text and len(text) > 5:
                specs.append(text)

    # If no <li>, try to extract key lines from descriptions
    if not specs and descriptions:
        for line in descriptions[0].split("."):
            line = line.strip()
            if 10 < len(line) < 120:
                specs.append(line)

    product["specs_ru"] = specs[:10]

    return product
