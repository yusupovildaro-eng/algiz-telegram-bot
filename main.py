"""
CLI entry point.

Usage:
  python main.py card              — post next unposted card (from algiz.uz catalog)
  python main.py card algiz        — post from algiz.uz catalog only
  python main.py card armas        — post from armaselektronik.com only
  python main.py card elina        — post from elina.ru only
  python main.py card --force      — post even if already posted
  python main.py init              — initialize DB
"""

import sys
from db import init_db

SOURCES = ["algiz"]
MANUAL_SOURCES = ["algiz", "armas", "elina"]


def _next_source() -> str:
    """Cycle through SOURCES."""
    from db import get_conn
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM kv WHERE key='last_source'").fetchone()
    last = row["value"] if row else SOURCES[-1]
    idx = SOURCES.index(last) if last in SOURCES else -1
    return SOURCES[(idx + 1) % len(SOURCES)]


def _save_source(source: str):
    from db import get_conn
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO kv (key, value) VALUES ('last_source', ?)",
            (source,)
        )


def _last_kv(key: str) -> str:
    from db import get_conn
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
    return row["value"] if row else ""


def _save_kv(key: str, value: str):
    from db import get_conn
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
            (key, value)
        )


def cmd_card(source: str | None = None, force: bool = False):
    from product_card import post_product_card
    from db import is_posted

    if source is None:
        source = _next_source()

    print(f"Source: {source}")

    if source == "algiz":
        from algiz_products import fetch_all_algiz_products, fetch_product_detail
        products = fetch_all_algiz_products()
    elif source == "elina":
        from elina_scraper import fetch_all_elina_products, fetch_product_detail
        products = fetch_all_elina_products(limit_per_category=20)
    else:
        from scraper import fetch_all_products, fetch_product_detail
        products = fetch_all_products(limit_per_category=10)

    last_category = _last_kv("last_category")
    last_supplier = _last_kv("last_supplier")
    unposted = [p for p in products if force or not is_posted(p["id"])]
    # Avoid posting two products in a row from the same category or the
    # same manufacturer.
    candidates = (
        [p for p in unposted if p.get("category") != last_category and p.get("supplier") != last_supplier]
        or [p for p in unposted if p.get("category") != last_category]
        or [p for p in unposted if p.get("supplier") != last_supplier]
        or unposted
    )

    for p in candidates:
        p = fetch_product_detail(p)
        ok = post_product_card(p, force=force)
        if ok:
            name = p.get("name_ru") or p.get("name_en") or p.get("name_tr", "?")
            print(f"Posted: {name} (category={p.get('category', '?')}, supplier={p.get('supplier', '?')})")
            _save_source(source)
            _save_kv("last_category", p.get("category", ""))
            _save_kv("last_supplier", p.get("supplier", ""))
            return

    print(f"No new products from {source}")


def main():
    init_db()

    args = sys.argv[1:]
    if not args or args[0] == "init":
        print("DB initialized.")
        return

    cmd = args[0]

    if cmd == "card":
        source = None
        if len(args) > 1 and args[1] in MANUAL_SOURCES:
            source = args[1]
        cmd_card(source=source, force="--force" in args)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
