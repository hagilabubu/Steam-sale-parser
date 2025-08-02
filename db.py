import mysql.connector
from mysql.connector import errorcode, pooling
from contextlib import closing
from config import DB_CONFIG

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS shop_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category TEXT,
    name TEXT,
    url TEXT,
    header_image TEXT,
    large_capsule_image TEXT,
    small_capsule_image TEXT,
    type TEXT,
    special_id TEXT,
    INDEX idx_special_id (special_id(255)),
    INDEX idx_type (type(10))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

INSERT_SQL = """
INSERT INTO shop_categories 
(category, name, url, header_image, large_capsule_image, small_capsule_image, type, special_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE 
    category=VALUES(category),
    name=VALUES(name),
    url=VALUES(url),
    header_image=VALUES(header_image),
    large_capsule_image=VALUES(large_capsule_image),
    small_capsule_image=VALUES(small_capsule_image),
    type=VALUES(type);
"""

# Создаем пул соединений один раз при загрузке модуля
connection_pool = pooling.MySQLConnectionPool(
    pool_name="steam_pool",
    pool_size=5,
    **DB_CONFIG
)

def _ensure_table():
    """Создаем таблицу, если она не существует"""
    try:
        with closing(connection_pool.get_connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE shop_categories;")
                cursor.execute(CREATE_TABLE_SQL)
            conn.commit()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Ошибка: Неверное имя пользователя или пароль")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Ошибка: База данных не существует")
        else:
            print(f"Ошибка при создании таблицы: {err}")
        raise

def save_batch(rows):
    """Сохраняем пачку записей в MySQL с использованием пула соединений"""
    _ensure_table()
    
    try:
        with closing(connection_pool.get_connection()) as conn:
            with conn.cursor() as cursor:
                cursor.executemany(INSERT_SQL, rows)
            conn.commit()
    except mysql.connector.Error as err:
        print(f"Ошибка при сохранении данных: {err}")
        raise