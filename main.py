"""
Точка входа микро-сервиса.
Можно запускать как:
$ python main.py
"""
from parser import fetch_all
from db import save_batch

if __name__ == "__main__":
    rows = fetch_all()
    if rows:
        # Преобразуем в список кортежей для executemany
        tuples = [(
            r["category"],
            r["name"],
            r["url"],
            r["header_image"],
            r["large_capsule_image"],
            r["small_capsule_image"],
            r["type"],
            r["special_id"],
        ) for r in rows]

        save_batch(tuples)
        print(f"[SUCCESS] Сохранено {len(tuples)} записей в shop_categories")
    else:
        print("[WARN] Нет данных для сохранения")