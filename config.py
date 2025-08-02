import os
from dotenv import load_dotenv
load_dotenv(encoding="utf-8")

# Изменяем конфигурацию для MySQL
DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),  # MySQL по умолчанию использует порт 3306
    database=os.getenv("DB_NAME", ""),     # В MySQL используется 'database' вместо 'dbname'
    user=os.getenv("DB_USER", ""),
    password=os.getenv("DB_PASS", ""),
    charset="utf8mb4",                     # Используем utf8mb4 для полной поддержки Unicode
)

# Остальные настройки остаются без изменений
STEAM_API_BASE = "https://store.steampowered.com/api"
FEATURED_URL = f"{STEAM_API_BASE}/featured"
FEATURED_CATEGORIES_URL = f"{STEAM_API_BASE}/featuredcategories"

CHROME_OPTIONS = [
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--lang=en-US",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-popup-blocking",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-component-extensions-with-background-pages",
    "--disable-features=PrivacySandboxSettings4,TriggeredResetProfileSettings",
]

REQUEST_DELAY = 1