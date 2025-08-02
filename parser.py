"""
Steam-sale HEADLESS parser
сбор: app / bundle / sub / DLC
работает даже если контент лениво подгружается
"""
import re, time, random, requests
from contextlib import suppress
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from config import (
    FEATURED_URL,
    FEATURED_CATEGORIES_URL,
    CHROME_OPTIONS,
    REQUEST_DELAY,
)

# ---------- REGEX ----------
RE_SALE_ID = re.compile(r"/sale/([^/?]+)")
RE_TYPE_ID = re.compile(r"/(app|bundle|sub|dlc)/(\d+)")

# ---------- UTILS ----------
def get_json(url: str) -> dict:
    return requests.get(url, timeout=30).json()

def extract_sale_ids_from_featured_categories() -> set[str]:
    data = get_json(FEATURED_CATEGORIES_URL)
    sale_ids = set()
    for block in data.values():
        if not isinstance(block, dict) or block.get("id") != "cat_spotlight":
            continue
        for item in block.get("items", []):
            m = RE_SALE_ID.search(item.get("url", ""))
            if m:
                sale_ids.add(m.group(1))
    return sale_ids

def build_driver():
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    opts = Options()
    for arg in CHROME_OPTIONS:
        opts.add_argument(arg)
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opts
    )
    driver.set_page_load_timeout(30)
    return driver

# ---------- SCROLL HELPERS ----------
def smooth_scroll(driver, steps: int = 6, step_pixels: int = 800, pause: float = 1.2):
    """Прокручиваем страницу заданное кол-во шагов, пока не достигнем конца."""
    for _ in range(steps):
        # запоминаем текущую высоту
        last_height = driver.execute_script("return document.body.scrollHeight")
        # прокручиваем вниз на step_pixels
        driver.execute_script(f"window.scrollBy(0, {step_pixels});")
        time.sleep(random.uniform(pause - 0.2, pause + 0.2))
        # проверяем, стала ли страница длиннее
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # дошли до конца

def wait_tab_switch(driver, retries: int = 3):
    """Ждём, пока вкладка Steam станет активной."""
    for _ in range(retries):
        with suppress(Exception):
            if "steampowered.com" in driver.current_url:
                time.sleep(random.uniform(1, 3))
                return
        time.sleep(1)

# ---------- PARSERS ----------
def parse_sale_page(sale_id: str) -> list[dict]:
    url = f"https://store.steampowered.com/sale/{sale_id}?cc=SE"
    driver = build_driver()
    try:
        driver.get(url)

        # Закрываем лишние вкладки
        main_handle = None
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if "steampowered.com/sale/" in driver.current_url:
                main_handle = handle
                break
        if main_handle:
            for h in driver.window_handles:
                if h != main_handle:
                    driver.switch_to.window(h)
                    driver.close()
            driver.switch_to.window(main_handle)
            wait_tab_switch(driver)

        # Плавная прокрутка + подгрузка
        smooth_scroll(driver)

        # Собираем ссылки
        selectors = (
            "a[href*='app/']",
            "a[href*='bundle/']",
            "a[href*='sub/']",
            "a[href*='dlc/']",
            "[data-panel] a[href*='bundle/']",
            "[data-panel] a[href*='sub/']",
            "._2eQ4mkpf4IzUp1e9NnM2Wr a",
            "._3r4Ny9tQdQZc50XDM5B2q2 a",
        )
        rows = []
        seen = set()

        for sel in selectors:
            for a in driver.find_elements(By.CSS_SELECTOR, sel):
                href = (a.get_attribute("href") or "").split("?")[0]
                m = RE_TYPE_ID.search(href)
                if not m:
                    continue
                t, sid = m.groups()
                if sid in seen:
                    continue
                seen.add(sid)

                name = a.text.strip()
                if not name:
                    with suppress(Exception):
                        name = a.find_element(By.TAG_NAME, "img").get_attribute("alt") or "Unknown"
                    if name == "Unknown":
                        continue

                imgs = a.find_elements(By.TAG_NAME, "img")
                header = large = small = ""
                for img in imgs:
                    src = img.get_attribute("src") or ""
                    if "hero_capsule" in src:
                        header = src
                    elif "616x353" in src:
                        large = src
                    elif "184x69" in src:
                        small = src
                if not large and imgs:
                    large = imgs[0].get_attribute("src")
                    small = large

                rows.append(
                    dict(
                        category=sale_id,
                        name=name,
                        url=href,
                        header_image=header,
                        large_capsule_image=large,
                        small_capsule_image=small,
                        type=t,
                        special_id=sid,
                    )
                )

        print(f"[DEBUG] Собрано {len(rows)} записей с sale-страницы {sale_id}")
        return rows

    except TimeoutException:
        print(f"[WARN] timeout на {url}")
        return []
    except Exception as e:
        print(f"[ERROR] {e}")
        return []
    finally:
        driver.quit()

# ---------- ENTRY ----------
def fetch_all() -> list[dict]:
    rows = []

    # 1. /api/featured
    featured = get_json(FEATURED_URL)
    for key, items in featured.items():
        if not isinstance(items, list):
            continue
        for it in items:
            if not it.get("name") or not it.get("id"):
                continue
            rows.append(
                dict(
                    category=key.replace("_", " ").title(),
                    name=it["name"],
                    url=f"https://store.steampowered.com/app/{it['id']}",
                    header_image=it.get("header_image", ""),
                    large_capsule_image=it.get("large_capsule_image", ""),
                    small_capsule_image=it.get("small_capsule_image", ""),
                    type="app",
                    special_id=str(it["id"]),
                )
            )

    # 2. sale pages
    sale_ids = extract_sale_ids_from_featured_categories()
    print(f"[INFO] Найдено {len(sale_ids)} sale-страниц")
    for idx, sale_id in enumerate(sale_ids, 1):
        print(f"[{idx}/{len(sale_ids)}] Парсим sale {sale_id}")
        rows.extend(parse_sale_page(sale_id))
        time.sleep(REQUEST_DELAY)

    return rows