import sqlite3
import json

DB = "products.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Товары
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT DEFAULT 'hot',
            discount INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )
    """)

    # Категории
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '🍽'
        )
    """)

    # Столы
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER NOT NULL,
            name TEXT
        )
    """)

    # Официанты
    cur.execute("""
        CREATE TABLE IF NOT EXISTS waiters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            percent REAL DEFAULT 6.0,
            active INTEGER DEFAULT 1,
            last_login INTEGER DEFAULT 0
        )
    """)

    # Профили пользователей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            guests INTEGER DEFAULT 1
        )
    """)

    # Заказы
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            waiter_id INTEGER DEFAULT 0,
            table_id INTEGER DEFAULT 0,
            items TEXT,
            subtotal REAL,
            service REAL,
            total REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Тестовые данные
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO categories (name, emoji) VALUES (?, ?)", [
            ("Горячее", "🍖"),
            ("Супы", "🍲"),
            ("Салаты", "🥗"),
            ("Напитки", "☕"),
        ])

    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)", [
            ("Шашлык из баранины", "Нежное мясо на углях", 2800, "hot"),
            ("Шурпа", "Наваристый суп с бараниной", 950, "soup"),
            ("Самса", "Слоёное тесто с мясом", 450, "hot"),
            ("Чайхана-плов", "Узбекский плов", 1200, "hot"),
            ("Ачичук", "Свежий салат из помидоров", 550, "salad"),
            ("Чай с чабрецом", "Горный чай с мёдом", 320, "drink"),
        ])

    cur.execute("SELECT COUNT(*) FROM tables")
    if cur.fetchone()[0] == 0:
        for i in range(1, 6):
            cur.execute("INSERT INTO tables (number, name) VALUES (?, ?)", (i, f"Стол {i}"))

    conn.commit()
    conn.close()

# ─── ПРОДУКТЫ ───
def get_products():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE active=1")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_products():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_product(name, description, price, category, discount=0):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, description, price, category, discount) VALUES (?, ?, ?, ?, ?)",
                (name, description, price, category, discount))
    conn.commit()
    conn.close()

def update_product(pid, name, description, price, category, discount, active):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE products SET name=?, description=?, price=?, category=?, discount=?, active=? WHERE id=?",
                (name, description, price, category, discount, active, pid))
    conn.commit()
    conn.close()

def delete_product(pid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
    conn.commit()
    conn.close()

# ─── КАТЕГОРИИ ───
def get_categories():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_category(name, emoji):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO categories (name, emoji) VALUES (?, ?)", (name, emoji))
    conn.commit()
    conn.close()

def delete_category(cid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE id=?", (cid,))
    conn.commit()
    conn.close()

# ─── СТОЛЫ ───
def get_tables():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM tables")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_table(number, name):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO tables (number, name) VALUES (?, ?)", (number, name))
    conn.commit()
    conn.close()

def delete_table(tid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM tables WHERE id=?", (tid,))
    conn.commit()
    conn.close()

# ─── ОФИЦИАНТЫ ───
def get_waiters():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM waiters WHERE active=1")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_waiter_by_user_id(user_id):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM waiters WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_waiter_by_name(name):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM waiters WHERE name=?", (name,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def add_waiter(name, password, percent):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO waiters (name, password, percent) VALUES (?, ?, ?)", (name, password, percent))
    conn.commit()
    conn.close()

def update_waiter_login(waiter_id, user_id):
    import time
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE waiters SET user_id=?, last_login=? WHERE id=?", (user_id, int(time.time()), waiter_id))
    conn.commit()
    conn.close()

def delete_waiter(wid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE waiters SET active=0 WHERE id=?", (wid,))
    conn.commit()
    conn.close()

# ─── ПОЛЬЗОВАТЕЛИ ───
def save_user(user_id, username, full_name, phone, guests):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, username, full_name, phone, guests)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            full_name=excluded.full_name,
            phone=excluded.phone,
            guests=excluded.guests
    """, (user_id, username, full_name, phone, guests))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# ─── ЗАКАЗЫ ───
def save_order(user_id, items, subtotal, service, total, waiter_id=0, table_id=0):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, waiter_id, table_id, items, subtotal, service, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, waiter_id, table_id, json.dumps(items, ensure_ascii=False), subtotal, service, total))
    conn.commit()
    conn.close()

def get_orders(user_id):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (user_id,))
    rows = cur.fetchall()
    conn.close()
    result = []
    for row in rows:
        r = dict(row)
        r['items'] = json.loads(r['items'])
        result.append(r)
    return result

def get_all_orders():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    result = []
    for row in rows:
        r = dict(row)
        r['items'] = json.loads(r['items'])
        result.append(r)
    return result

def get_waiter_stats():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT w.id, w.name, w.percent,
               COUNT(o.id) as order_count,
               COALESCE(SUM(o.total), 0) as total_sum
        FROM waiters w
        LEFT JOIN orders o ON o.waiter_id = w.id
        WHERE w.active=1
        GROUP BY w.id
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]