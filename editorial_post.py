"""
Generate and post editorial content.

Types:
  - review   — detailed review of one product
  - tips     — tips on choosing warning/siren equipment
  - compare  — compare 2 products
  - digest   — weekly digest of products
"""

import re
import random
from claude_client import generate
from telegram_client import send_text
from db import log_editorial
from scraper import fetch_all_products, fetch_product_detail

POST_TYPES = ["review", "tips", "compare", "digest"]
SHOP_LINK = "https://algiz.uz/ru"

MANAGER_LINK = "https://t.me/www_aloqa_uz"
CTA = (
    f'\n\n💬 <a href="{MANAGER_LINK}">Связаться с менеджером для подробностей</a>'
    f'\n🔗 <a href="{SHOP_LINK}">Подробнее / заказать</a>'
)

RULES = """
Строгие требования к тексту:
- Только русский язык. Никаких иностранных слов — всё переводить: "балка СГУ" вместо "light bar", "степень защиты IP65" вместо просто "IP65", "стандарт ЕЭК ООН R65" вместо "ECE R65", "многоцветный" вместо "multicolor", "светодиодный маяк" вместо "LED beacon"
- Никаких символов **, *, __, #
- Никаких markdown-символов
- Живой профессиональный стиль
"""


def _clean(text: str) -> str:
    text = text.replace('**', '').replace('__', '')
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'(?<!\S)\*(?!\s)', '', text)
    text = re.sub(r'(?<!\*)\*(?!\S)', '', text)
    return text.strip()


def _review_prompt(product: dict) -> str:
    features = "\n".join(f"- {f}" for f in product.get("features_tr", [])[:10])
    return f"""Напиши экспертный пост-обзор для Telegram-канала о сигнальном оборудовании.

Турецкое название (переведи): {product.get('name_tr', '')}
Описание (TR, переведи): {product.get('description_tr', '')[:400]}
Характеристики (TR, переведи):
{features}

Структура поста:
1. Цепляющий заголовок (не слово "Обзор")
2. Для кого / где применяется
3. Главные плюсы (2-3 пункта с ✅)
4. На что обратить внимание

Длина: 180-240 слов.
{RULES}"""


def _tips_prompt(products: list[dict]) -> str:
    names = ", ".join(p.get("name_tr", "") for p in products[:5])
    return f"""Напиши полезный пост с советами для покупателей из Узбекистана и СНГ.
Тема: как выбрать световую сигнальную систему для спецавтомобиля.

Упомяни 2-3 наших товара (переведи названия с турецкого): {names}

Структура:
- Короткое вступление
- 3-4 практических совета с заголовками
- Конкретные критерии выбора

Длина: 180-220 слов.
{RULES}"""


def _compare_prompt(p1: dict, p2: dict) -> str:
    return f"""Напиши пост-сравнение двух товаров для Telegram-канала.

Товар 1 (переведи название): {p1.get('name_tr', '')}
Особенности (переведи): {'; '.join(p1.get('features_tr', [])[:5])}

Товар 2 (переведи название): {p2.get('name_tr', '')}
Особенности (переведи): {'; '.join(p2.get('features_tr', [])[:5])}

Структура:
- Заголовок с названиями двух моделей
- 2-3 ключевых отличия с буллетами 🔹
- Итог: кому какой подойдёт

Длина: 160-200 слов.
{RULES}"""


def _digest_prompt(products: list[dict]) -> str:
    lines = "\n".join(f"- {p.get('name_tr', '?')}" for p in products[:6])
    return f"""Напиши еженедельный дайджест товаров для Telegram-канала.

Товары (переведи названия с турецкого):
{lines}

Структура:
- Короткое вступление (1-2 предложения)
- Список товаров с переведёнными названиями и коротким описанием каждого (1 строка)

Длина: 140-180 слов.
{RULES}"""


def post_editorial(post_type: str | None = None) -> str:
    if post_type is None:
        post_type = random.choice(POST_TYPES)

    products = fetch_all_products(limit_per_category=5)
    if not products:
        raise RuntimeError("No products fetched")

    if post_type == "review":
        product = random.choice(products)
        product = fetch_product_detail(product)
        prompt = _review_prompt(product)
        topic = f"review:{product['id']}"

    elif post_type == "tips":
        prompt = _tips_prompt(products)
        topic = "tips"

    elif post_type == "compare" and len(products) >= 2:
        p1, p2 = random.sample(products, 2)
        p1 = fetch_product_detail(p1)
        p2 = fetch_product_detail(p2)
        prompt = _compare_prompt(p1, p2)
        topic = f"compare:{p1['id']}:{p2['id']}"

    else:
        prompt = _digest_prompt(products)
        topic = "digest"

    text = _clean(generate(prompt, max_tokens=500)) + CTA
    send_text(text)
    log_editorial(topic)
    return topic
