import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SHOP_URL = os.environ.get("SHOP_URL", "https://www.armaselektronik.com/tr")

# Sub-category pages that contain actual products
CATALOG_CATEGORIES = [
    # Световые и сирены
    "/tepe-lambalari",
    "/mini-tepe-lambalari",
    "/motosiklet-ikaz-sistemleri",
    "/mini-ikaz-lambalari",
    "/silindirik-ikaz-lambalari",
    "/miknatisfli-ikaz-lambalari",
    "/trafik-yonlendirme-lambalari",
    "/siren-anons-sistemleri",
    "/hoparlorler",
    "/el-feneri-ve-projektorler",
    "/arac-ici-aydinlatma",
    "/interkom-sistemleri",
    # Алкотестеры
    "/profesyonel-alkolmetreler",
    "/temassiz-olcum-alkolmetreler",
    "/arac-alkolmetreleri-interlock",
    "/kisisel-olcum-alkolmetreler",
    # Наркотесты
    "/uyusturucu-olcum-sistemleri",
]

CHANNEL_VOICE = """
Ты — редактор Telegram-канала aloqa.uz — магазина оборудования безопасности и сигнальных систем
(проблесковые маяки, мигалки, сирены, алкотестеры).
Аудитория: сотрудники силовых структур, коммунальные службы, таксопарки, частные покупатели — Узбекистан и СНГ.
Стиль: профессиональный, конкретный, живой. Без канцелярита.
Язык ответа: РУССКИЙ. Переводи с турецкого на русский.
Эмодзи: 1-2 уместных, не больше.
"""
