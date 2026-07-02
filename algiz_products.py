"""
Loader for algiz.uz's own product catalog (data/algiz_products.json).

Unlike the armas/elina scrapers, this is not scraped live — it's a snapshot
of the products array from algiz-new's lib/data.ts, restricted to the
categories we post about (sgu, sirens, lightbars, breathalyzers). Images are
served directly from the live site, so no re-download / referer tricks needed.
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IMAGE_BASE = "https://algiz.uz"

COUNTRY = {
    "armas": "🇹🇷 Ishlab chiqaruvchi: Turkiya",
    "elina": "🇷🇺 Ishlab chiqaruvchi: Rossiya",
    "granda": "🇨🇳 Ishlab chiqaruvchi: Xitoy",
}


def fetch_all_algiz_products() -> list[dict]:
    path = os.path.join(DATA_DIR, "algiz_products.json")
    with open(path, encoding="utf-8") as f:
        items = json.load(f)

    products = []
    for item in items:
        image = item.get("image", "")
        products.append({
            "id": "algiz_" + item["id"],
            "product_url": f"https://algiz.uz/ru/products/{item['id']}",
            "name_ru": item.get("name", ""),
            "description_ru": item.get("description", ""),
            "specs_ru": item.get("features") or item.get("specs") or [],
            "image_url": IMAGE_BASE + image if image else "",
            "gallery_images": [IMAGE_BASE + image] if image else [],
            "source": "algiz",
            "supplier": item.get("supplier", ""),
        })
    return products


def fetch_product_detail(product: dict) -> dict:
    """No-op: algiz_products.json already contains full product data."""
    return product
