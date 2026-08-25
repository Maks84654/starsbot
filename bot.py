import os
import asyncio
import logging
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (ЧТОБЫ НЕ ПАДАЛ ПО ПОРТУ) ---
async def handle(request):
    return web.Response(text="I'm alive!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 10000)))
    await site.start()

# --- НАСТРОЙКИ БОТА ---
API_TOKEN = "8615635837:AAEGq_qwyjMRNhbp8LVORJHgxL5vclAg6jg"
MANAGER_USERNAME = "@StarsManagerr"
BOT_USERNAME = "StarsBiest_bot"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- СОСТОЯНИЯ FSM ---
class OrderState(StatesGroup):
    waiting_for_quantity = State()

# --- ТЕКСТЫ И ИНСТРУКЦИИ ---
WELCOME_TEXT = (
    "Добро пожаловать!!!\n\n"
    "StarsBiest🌟\n"
    "Бот в котором ты можешь купить брученные монеты по цене ниже рынка📊\n\n"
    f"Реклама/сотрудничество :{MANAGER_USERNAME}"
)

GUARANTEES_TEXT = (
    "ГАРАНТИИ И БЕЗОПАСНОСТЬ СДЕЛОК\n\n"
    "Мы дорожим своей репутацией и обеспечиваем максимальную прозрачность при проведении сделок на любые суммы.\n\n"
    "Официальный Договор (от 20 000 ₽):\n"
    "При покупке объемов от 15-20 активов по вашему желанию оформляем Договор передачи цифровых активов (в формате .docx / .pdf).\n\n"
    "Сделка частями (Транши):\n"
    "При первой покупке или крупном чеке готовы разбить объем на несколько частей.\n\n"
    f"Оформить договор или задать вопрос: {MANAGER_USERNAME}"
)

CONTRACT_TEXT = (
    "Порядок оформления договора:\n\n"
    "1. Согласование данных\n"
    "Вы передаете менеджеру данные для заполнения: ФИО и объем активов.\n\n"
    "2. Подготовка документа\n"
    "Мы формируем официальный договор и отправляем вам файл.\n\n"
    "📄 <a href='https://1drv.ms/w/c/b68296d9a1b801f9/IQCssXFpGbMRQ62ugKJ-f1S3AVVz8N8888gTZVzAgbp6e3E'>Посмотреть пример договора</a>\n\n"
    f"По всем вопросам: {MANAGER_USERNAME}"
)

HELP_TEXT = (
    "💡 Как оплачивать?\n\n"
    "1️⃣ Выберите нужный товар в каталоге или разделе бирж, укажите количество — бот выдаст готовую карточку заказа.\n\n"
    "2️⃣ Как купить крипту на Xroket:\n"
    "Перейдите на биржу **Xroket** и приобретите нужную сумму. "
    "®️ Верификация и 18 лет не обязательны, можно спокойно пользоваться без этого ®️\n"
    "После покупки создайте внутри биржи криптовалютный чек (ваучер) на сумму заказа.\n\n"
    "3️⃣ Отправка чека:\n"
    "Перешлите карточку заказа вместе со ссылкой на созданный чек нашему менеджеру: " + MANAGER_USERNAME + "\n"
    "Менеджер просто активирует его в один клик, после чего сразу выдаст вам товар! 👨‍💻"
)

# --- БАЗА ТОВАРОВ И ЦЕН ---
PRODUCT_DATA = {
    "metis": {"name": "METIS", "price": 1450, "is_usd": False},
    "agave": {"name": "AGAVE", "price": 1830, "is_usd": False},
    "avto": {"name": "AVTO", "price": 1055, "is_usd": False},
    "software": {"name": "SOFTWARE", "price": 250, "is_usd": True},
    "atronix": {"name": "ATRONIX", "price": 35, "is_usd": True},
    "brexit": {"name": "BREXIT", "price": 35, "is_usd": True}
}

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог монет", callback_data="catalog")],
        [InlineKeyboardButton(text="📊 Аккаунты биржи", callback_data="section_accounts")],
        [InlineKeyboardButton(text="💡 Как оплачивать?", callback_data="help_info")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="🛡 Гарантии", callback_data="guarantees")]
    ])

def get_catalog_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍀 Metis Coin", callback_data="metis"),
         InlineKeyboardButton(text="🔰 Agave Coin", callback_data="agave")],
        [InlineKeyboardButton(text="🌚 Avto Coin", callback_data="avto"),
         InlineKeyboardButton(text="✨ Персональный софт", callback_data="software")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])

def get_accounts_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Биржа Atronix", callback_data="atronix"),
         InlineKeyboardButton(text="📈 Биржа BreXIT", callback_data="brexit")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])

# --- УНИВЕРСАЛЬНАЯ ОТПРАВКА С ФОТО ---
async def edit_or_send_photo(callback: types.CallbackQuery, photo_path: str, caption: str, reply_markup: InlineKeyboardMarkup, parse_mode: str = None):
    try:
        media = InputMediaPhoto(media=FSInputFile(photo_path), caption=caption, parse_mode=parse_mode)
        await callback.message.edit_media(media=media, reply_markup=reply_markup)
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(photo=FSInputFile(photo_path), caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("image19.jfif")
        await message.answer_photo(photo=photo, caption=WELCOME_TEXT, reply_markup=get_main_menu())
    except Exception:
        await message.answer(WELCOME_TEXT, reply_markup=get_main_menu())

@dp.message(Command("help"))
async def cmd_help(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("image19.jfif")
        await message.answer_photo(photo=photo, caption=HELP_TEXT, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main")]
        ]))
    except Exception:
        await message.answer(HELP_TEXT)

@dp.callback_query(F.data == "help_info")
async def show_help_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await edit_or_send_photo(callback, "image19.jfif", HELP_TEXT, kb)

@dp.callback_query(F.data == "back_main")
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await edit_or_send_photo(callback, "image19.jfif", WELCOME_TEXT, get_main_menu())

@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "Каталог цифровых товаров и монет. Выберите интересующую позицию:"
    await edit_or_send_photo(callback, "image14.jfif", text, get_catalog_menu())

@dp.callback_query(F.data == "section_accounts")
async def show_accounts_section(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "Аккаунты бирж:\nВыберите доступный вариант:"
    await edit_or_send_photo(callback, "image14.jfif", text, get_accounts_menu())

@dp.callback_query(F.data.in_({"metis", "agave", "avto", "software"}))
async def show_product(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.data == "metis":
        text = (
            "Metis Coin – оптимистичная монета обеспечивающая безопасность и масштабность протокола.\n"
            "📉 Цена одной BRUT монеты - 1450₽\n"
            "📈 Цена монеты на бирже - 3147₽\n\n"
            f"Для заказа, напишите менеджеру : {MANAGER_USERNAME}"
        )
        photo_file = "image16.jfif"
    elif callback.data == "agave":
        text = (
            "Agave Coin — это утилит токен для развития индустрии полезных культур.\n"
            "📉 Цена одной BRUT монеты - 1830₽\n"
            "📈 Цена монеты на бирже - 4237₽\n\n"
            f"Для заказа, напишите менеджеру : {MANAGER_USERNAME}"
        )
        photo_file = "image17.jfif"
    elif callback.data == "avto":
        text = (
            "Avto Coin - агрегатор урожайного земледелия на Binance Smart Chain.\n"
            "📉 Цена одной BRUT монеты - 1055₽\n"
            "📈 Цена монеты на бирже - 1863₽\n\n"
            f"Для заказа, напишите менеджеру : {MANAGER_USERNAME}"
        )
        photo_file = "image15.jfif"
    elif callback.data == "software":
        text = (
            "Персональный софт от команды Stars\n\n"
            "Преимущества софта:\n- Скорость 🚀\n- Валидность 🌟\n- Легкость ✅\n\n"
            "Цена: 250$\n\n"
            f"👨‍💻 Менеджер: {MANAGER_USERNAME}"
        )
        photo_file = "image19.jfif"

    buy_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить 🛒", callback_data=f"buy_{callback.data}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog")]
    ])
    await edit_or_send_photo(callback, photo_file, text, buy_kb)

@dp.callback_query(F.data.in_({"atronix", "brexit"}))
async def show_exchange_product(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.data == "atronix":
        item_name = "Atronix"
        photo_file = "image11.jfif"
    else:
        item_name = "BreXIT"
        photo_file = "image12.jfif"
        
    text = (
        f"Цифровой аккаунт закрытой биржи {item_name} с пройденной верификацией.\n\n"
        "📉 Фиксированная цена — 35$.\n\n"
        f"Для приобретения обратитесь к менеджеру: {MANAGER_USERNAME}"
    )
    buy_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить 🛒", callback_data=f"buy_{callback.data}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="section_accounts")]
    ])
    await edit_or_send_photo(callback, photo_file, text, buy_kb)

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy_click(callback: types.CallbackQuery, state: FSMContext):
    item_type = callback.data.split("_")[1]
    await state.update_data(item_type=item_type)
    await state.set_state(OrderState.waiting_for_quantity)
    
    back_target = "section_accounts" if item_type in {"atronix", "brexit"} else "catalog"
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data=back_target)]
    ])
    
    text = "Какое количество вы хотите заказать?\n\nВведите количество цифрами:"
    await edit_or_send_photo(callback, "image14.jfif", text, back_kb)

@dp.message(OrderState.waiting_for_quantity)
async def process_quantity_input(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректное число цифрами:")
        return
        
    quantity = int(message.text)
    data = await state.get_data()
    item_type = data.get("item_type")
    await state.clear()
    
    prod_info = PRODUCT_DATA.get(item_type, {"name": "TOVAR", "price": 1000, "is_usd": False})
    total_price = quantity * prod_info["price"]
    
    price_str = f"{total_price} $" if prod_info["is_usd"] else f"{total_price:.2f} ₽"
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    order_card_text = (
        f"{current_date}\n"
        f"🔹 ID заказчика - {message.from_user.id}\n"
        f"🔸 Выбранная монета - {prod_info['name']}\n"
        f"🔹 Количество монет - {quantity}\n"
        f"🛒 Сумма заказа: {price_str}\n\n"
        f"⚠️ Для получения товара и оплаты заказа, перешлите данное сообщение менеджеру\n"
        f"👨‍💻 Менеджер:\n{MANAGER_USERNAME}"
    )
    
    finish_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])
    
    try:
        photo = FSInputFile("image14.jfif")
        await message.answer_photo(photo=photo, caption=order_card_text, reply_markup=finish_kb)
    except Exception:
        await message.answer(order_card_text, reply_markup=finish_kb)

@dp.callback_query(F.data == "guarantees")
async def show_guarantees(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Как оформляется договор?", callback_data="contract_info")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await edit_or_send_photo(callback, "image13.jfif", GUARANTEES_TEXT, kb)

@dp.callback_query(F.data == "contract_info")
async def show_contract_info(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="guarantees")]
    ])
    await edit_or_send_photo(callback, "image13.jfif", CONTRACT_TEXT, kb, parse_mode="HTML")

@dp.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery, state: FsmContext if 'FsmContext' in globals() else FSMContext):
    await state.clear()
    user = callback.from_user
    username = f"@{user.username}" if user.username else "Отсутствует"
    ref_code = "107922"
    ref_link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"
    
    profile_text = (
        "Ваш аккаунт:\n\n"
        f"Username: {username}\n"
        f"ID: {user.id}\n"
        f"Реферальный код: {ref_code}\n\n"
        f"🔗 Ваша реферальная ссылка:\n{ref_link}"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await edit_or_send_photo(callback, "image13.jfif", profile_text, back_kb)

# --- ОСНОВНОЙ ЗАПУСК (БОТ + ВЕБ-СЕРВЕР) ---
async def main():
    asyncio.create_task(start_web_server())
    print("Бот запущен и полностью готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
