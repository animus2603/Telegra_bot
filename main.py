import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from database import *

BOT_TOKEN = "7620485199:AAH_nrqIqNmHT6K5mdw07JdBAAxERkGKOV4"
SELLER_CHAT_ID = "5631009914"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
init_db()

# ─── ПРОДУКТЫ ───
@app.get("/api/products")
def api_products():
    return get_products()

@app.get("/api/products/all")
def api_all_products():
    return get_all_products()

class ProductModel(BaseModel):
    name: str
    description: str = ""
    price: float
    category: str
    discount: int = 0

@app.post("/api/products")
def api_add_product(p: ProductModel):
    add_product(p.name, p.description, p.price, p.category, p.discount)
    return {"status": "ok"}

class ProductUpdateModel(BaseModel):
    name: str
    description: str = ""
    price: float
    category: str
    discount: int = 0
    active: int = 1

@app.put("/api/products/{pid}")
def api_update_product(pid: int, p: ProductUpdateModel):
    update_product(pid, p.name, p.description, p.price, p.category, p.discount, p.active)
    return {"status": "ok"}

@app.delete("/api/products/{pid}")
def api_delete_product(pid: int):
    delete_product(pid)
    return {"status": "ok"}

# ─── КАТЕГОРИИ ───
@app.get("/api/categories")
def api_categories():
    return get_categories()

class CategoryModel(BaseModel):
    name: str
    emoji: str = "🍽"

@app.post("/api/categories")
def api_add_category(c: CategoryModel):
    add_category(c.name, c.emoji)
    return {"status": "ok"}

@app.delete("/api/categories/{cid}")
def api_delete_category(cid: int):
    delete_category(cid)
    return {"status": "ok"}

# ─── СТОЛЫ ───
@app.get("/api/tables")
def api_tables():
    return get_tables()

class TableModel(BaseModel):
    number: int
    name: str = ""

@app.post("/api/tables")
def api_add_table(t: TableModel):
    add_table(t.number, t.name or f"Стол {t.number}")
    return {"status": "ok"}

@app.delete("/api/tables/{tid}")
def api_delete_table(tid: int):
    delete_table(tid)
    return {"status": "ok"}

# ─── ОФИЦИАНТЫ ───
@app.get("/api/waiters")
def api_waiters():
    return get_waiters()

@app.get("/api/waiters/stats")
def api_waiter_stats():
    return get_waiter_stats()

class WaiterModel(BaseModel):
    name: str
    password: str
    percent: float = 6.0

@app.post("/api/waiters")
def api_add_waiter(w: WaiterModel):
    add_waiter(w.name, w.password, w.percent)
    return {"status": "ok"}

@app.delete("/api/waiters/{wid}")
def api_delete_waiter(wid: int):
    delete_waiter(wid)
    return {"status": "ok"}

# ─── ПОЛЬЗОВАТЕЛИ ───
@app.get("/api/user/{user_id}")
def api_get_user(user_id: int):
    user = get_user(user_id)
    if user:
        return user
    return {"error": "not found"}

@app.get("/api/orders/{user_id}")
def api_get_orders(user_id: int):
    return get_orders(user_id)

# ─── ВСЕ ЗАКАЗЫ (для админа) ───
@app.get("/api/orders")
def api_all_orders():
    return get_all_orders()

# ─── СОЗДАТЬ ЗАКАЗ ───
class Order(BaseModel):
    user_id: int
    username: str
    items: list
    subtotal: float = 0
    service: float = 0
    total: float = 0
    waiter_id: Optional[int] = 0
    table_id: Optional[int] = 0

@app.post("/api/order")
async def create_order(order: Order):
    user = get_user(order.user_id)
    full_name = user['full_name'] if user else f"@{order.username}"
    phone = user['phone'] if user else "—"
    guests = user['guests'] if user else "—"

    # Имя официанта
    waiter_name = "—"
    if order.waiter_id:
        waiters = get_waiters()
        w = next((x for x in waiters if x['id'] == order.waiter_id), None)
        if w:
            waiter_name = w['name']

    # Имя стола
    table_name = "—"
    if order.table_id:
        tables = get_tables()
        t = next((x for x in tables if x['id'] == order.table_id), None)
        if t:
            table_name = t['name']

    lines = [
        "🍽 *Новый заказ*", "",
        f"👤 Гость: {full_name}",
        f"📞 Телефон: {phone}",
        f"🪑 Гостей: {guests}",
        f"🏷 Стол: {table_name}",
        f"👨‍🍳 Официант: {waiter_name}",
        "", "📋 *Заказ:*",
    ]

    for item in order.items:
        lines.append(f"• {item['name']} ×{item['qty']} — {int(item['price'] * item['qty'])} ₸")

    lines += [
        "",
        f"💵 Сумма блюд: {int(order.subtotal)} ₸",
        f"🔖 Обслуживание (15%): {int(order.service)} ₸",
        f"💰 *Итого: {int(order.total)} ₸*",
    ]

    message = "\n".join(lines)

    save_order(
        order.user_id, order.items,
        order.subtotal, order.service, order.total,
        order.waiter_id or 0, order.table_id or 0
    )

    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": SELLER_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        )

    return {"status": "ok"}