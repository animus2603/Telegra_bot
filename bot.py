import asyncio
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import (Message, InlineKeyboardMarkup, InlineKeyboardButton,
                            WebAppInfo, ReplyKeyboardMarkup, KeyboardButton,
                            ReplyKeyboardRemove)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from database import (save_user, get_user, init_db, get_waiter_by_name,
                      get_waiter_by_user_id, update_waiter_login)

BOT_TOKEN = "7620485199:AAH_nrqIqNmHT6K5mdw07JdBAAxERkGKOV4"
ADMIN_ID = 5631009914  # твой Telegram ID
WEB_APP_URL = "https://numerous-citadel-feminine.ngrok-free.dev/static/index.html"
ADMIN_URL = "https://numerous-citadel-feminine.ngrok-free.dev/static/admin.html"

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
init_db()

# ─── Состояния ───
class Registration(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_guests = State()

class WaiterLogin(StatesGroup):
    waiting_name = State()
    waiting_password = State()

# ─── /start ───
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)

    if user:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEB_APP_URL))]
        ])
        if message.from_user.id == ADMIN_ID:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEB_APP_URL))],
                [InlineKeyboardButton(text="⚙️ Админ панель", web_app=WebAppInfo(url=ADMIN_URL))]
            ])
        await message.answer(
            f"С возвращением, *{user['full_name']}*! 🌙",
            parse_mode="Markdown", reply_markup=kb
        )
    else:
        await state.set_state(Registration.waiting_name)
        await message.answer(
            "🌙 Добро пожаловать в ресторан *Аль-Машрик*!\n\nКак вас зовут?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )

# ─── Регистрация ───
@dp.message(Registration.waiting_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(Registration.waiting_phone)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer(
        f"Приятно познакомиться, *{message.text}*! ✨\n\nПоделитесь номером телефона:",
        parse_mode="Markdown", reply_markup=kb
    )

@dp.message(Registration.waiting_phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(Registration.waiting_guests)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="6")],
            [KeyboardButton(text="7"), KeyboardButton(text="8"), KeyboardButton(text="9")],
        ],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Сколько гостей будет за столом? 🪑", reply_markup=kb)

@dp.message(Registration.waiting_phone)
async def get_phone_text(message: Message):
    await message.answer("Пожалуйста нажмите кнопку 📱 *Поделиться номером* ниже:", parse_mode="Markdown")

@dp.message(Registration.waiting_guests)
async def get_guests(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста выберите кнопку ниже 👇")
        return
    data = await state.get_data()
    guests = int(message.text)
    save_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=data['full_name'],
        phone=data['phone'],
        guests=guests
    )
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    if message.from_user.id == ADMIN_ID:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEB_APP_URL))],
            [InlineKeyboardButton(text="⚙️ Админ панель", web_app=WebAppInfo(url=ADMIN_URL))]
        ])

    await message.answer(
        f"Всё готово! 🌙\n\n"
        f"👤 Имя: *{data['full_name']}*\n"
        f"📞 Телефон: *{data['phone']}*\n"
        f"🪑 Гостей: *{guests}*\n\n"
        f"Добро пожаловать!",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await asyncio.sleep(1)
    await message.answer("Нажмите чтобы открыть меню 👇", reply_markup=kb)

# ─── /ofik — вход официанта ───
@dp.message(Command("ofik"))
async def waiter_login_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    # Проверяем уже залогинен ли
    waiter = get_waiter_by_user_id(user_id)
    if waiter:
        # Проверяем не прошло ли 2 дня
        two_days = 2 * 24 * 60 * 60
        if time.time() - waiter['last_login'] < two_days:
            await message.answer(
                f"✅ Вы вошли как официант *{waiter['name']}*\n"
                f"Процент: *{waiter['percent']}%*",
                parse_mode="Markdown"
            )
            return

    # Нужен пароль
    await state.set_state(WaiterLogin.waiting_name)
    await message.answer(
        "👨‍🍳 Вход для официантов\n\nВведите ваше имя:",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(WaiterLogin.waiting_name)
async def waiter_name(message: Message, state: FSMContext):
    waiter = get_waiter_by_name(message.text.strip())
    if not waiter:
        await message.answer("❌ Официант с таким именем не найден. Попробуйте снова:")
        return
    await state.update_data(waiter_id=waiter['id'], waiter_name=waiter['name'])
    await state.set_state(WaiterLogin.waiting_password)
    await message.answer("🔑 Введите пароль:")

@dp.message(WaiterLogin.waiting_password)
async def waiter_password(message: Message, state: FSMContext):
    data = await state.get_data()
    waiter = get_waiter_by_name(data['waiter_name'])

    if not waiter or waiter['password'] != message.text.strip():
        await message.answer("❌ Неверный пароль. Попробуйте снова:")
        return

    update_waiter_login(waiter['id'], message.from_user.id)
    await state.clear()
    await message.answer(
        f"✅ Добро пожаловать, *{waiter['name']}*!\n"
        f"Ваш процент: *{waiter['percent']}%*\n\n"
        f"Сессия активна 2 дня.",
        parse_mode="Markdown"
    )

# ─── /admin — быстрый доступ ───
@dp.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Открыть админ панель", web_app=WebAppInfo(url=ADMIN_URL))]
    ])
    await message.answer("Добро пожаловать в админ панель 👇", reply_markup=kb)

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "📌 Команды:\n"
        "/start — открыть меню\n"
        "/ofik — вход для официантов\n"
        "/help — помощь"
    )

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())