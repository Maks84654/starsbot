import asyncio
import logging
import os
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
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
    "✨ <b>Добро пожаловать в StarsBiest!</b> ✨\n\n"
    "Бот, в котором ты можешь купить брученные монеты по цене ниже рынка 📊\n\n"
    f"Реклама / сотрудничество: {MANAGER_USERNAME}"
)

GUARANTEES_TEXT = (
    "🛡️ ГАРАНТИИ И БЕЗОПАСНОСТЬ СДЕЛОК\n\n"
    "Мы дорожим своей репутацией и обеспечиваем максимальную прозрачность при проведении сделок на любые суммы.\n\n"
    "📄 Официальный Договор (от 20 000 ₽):\n"
    "При покупке объемов от 15-20 активов по вашему желанию оформляем Договор передачи цифровых активов (в формате .docx / .pdf).\n\n"
    "🔄 Сделка частями (Транши):\n"
    "При первой покупке или крупном чеке готовы разбить объем на несколько частей.\n\n"
    f"Оформить договор или задать вопрос: {MANAGER_USERNAME}"
)

CONTRACT_TEXT = (
    "📋 Порядок оформления договора:\n\n"
    "1. Согласование данных\n"
    "Вы передаете менеджеру данные для заполнения: ФИО и объем активов.\n\n"
    "2. Подготовка документа\n"
    "Мы формируем официальный договор и отправляем вам файл.\n\n"
    "📄 <a href='https://1drv.ms/b/c/b68296d9a1b801f9/IQCf50IgNgmtRI9viF9HlqhfAQRjUe6MB_2kdNfBWGRX_dE'>Посмотреть пример договора</a>\n\n"
    f"По всем вопросам: {MANAGER_USERNAME}"
)

HELP_TEXT = (
    "💡 <b>Как оплачивать?</b>\n\n"
    "1️⃣ Выберите нужный товар в каталоге или разделе бирж, укажите количество — бот выдаст готовую карточку заказа.\n\n"
    "2️⃣ <b>Как купить крипту на Xroket:</b>\n"
    "Перейдите на биржу <b>Xroket</b> и приобретите нужную сумму. "
    "®️ Верификация и 18 лет не обязательны, можно спокойно пользоваться без этого ®️\n"
    "После покупки создайте внутри биржи криптовалютный чек (ваучер) на сумму заказа.\n\n"
    "3️⃣ <b>Отправка чека:</b>\n"
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
        [InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral")],
        [InlineKeyboardButton(text="❓ FAQ (Частые вопросы)", callback_data="faq")],
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

# --- ОТПРАВКА НОВЫХ СООБЩЕНИЙ БЕЗ УДАЛЕНИЯ ИСТОРИИ ---
async def show_new_screen(callback: types.CallbackQuery, photo_path: str, text: str, reply_markup: InlineKeyboardMarkup):
    try:
        photo = FSInputFile(photo_path)
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer() # Убираем часики с кнопки

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        photo = FSInputFile("image19.jfif")
        await message.answer_photo(photo=photo, caption=WELCOME_TEXT, reply_markup=get_main_menu(), parse_mode="HTML")
    except Exception:
        await message.answer(WELCOME_TEXT, reply_markup=get_main_menu(), parse_mode="HTML")

@dp.message(Command("referral"))
async def cmd_referral(message: types.Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user.id}"
    
    keyboard = [
        [InlineKeyboardButton(text="📞 Написать менеджеру", url="https://t.me/StarsManagerr")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ]
    
    ref_text = (
        "ℹ️ <b>Информация о реферальной системе</b> 💶\n\n"
        "На данный момент у нас действует реферальная система, с помощью которой вы сможете получить <b>5 любых бесплатных монет</b>!\n\n"
        "Для этого вам нужно привести к нам любого человека и дать ему свой персональный реферальный код.\n\n"
        "📌 <b>Условие:</b> приведенный вами человек должен совершить покупку минимум <b>20 любых монет</b> в нашем боте.\n\n"
        f"🔗 <b>Ваша индивидуальная реферальная ссылка:</b>\n<a href='{ref_link}'>{ref_link}</a>\n\n"
        "Для получения и подтверждения бонусов пишите напрямик: @StarsManagerr"
    )
    
    try:
        await message.answer_photo(photo=FSInputFile("image18.jfif"), caption=ref_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    except Exception:
        await message.answer(ref_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

@dp.message(Command("help"))
async def cmd_help(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_main")]])
    try:
        photo = FSInputFile("image14.jfif")
        await message.answer_photo(photo=photo, caption=HELP_TEXT, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await message.answer(HELP_TEXT, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "help_info")
async def show_help_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]])
    await show_new_screen(callback, "image14.jfif", HELP_TEXT, kb)

@dp.callback_query(F.data == "back_main")
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_new_screen(callback, "image19.jfif", WELCOME_TEXT, get_main_menu())

@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "Каталог цифровых товаров и монет. Выберите интересующую позицию:"
    await show_new_screen(callback, "image14.jfif", text, get_catalog_menu())

@dp.callback_query(F.data == "section_accounts")
async def show_accounts_section(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "Аккаунты бирж:\nВыберите доступный вариант:"
    await show_new_screen(callback, "image14.jfif", text, get_accounts_menu())

@dp.callback_query(F.data == "referral")
async def show_referral_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user = callback.from_user
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user.id}"
    
    ref_text = (
        "ℹ️ <b>Информация о реферальной системе</b> 💶\n\n"
        "На данный момент у нас действует реферальная система, с помощью которой вы сможете получить <b>5 любых бесплатных монет</b>!\n\n"
        "Для этого вам нужно привести к нам любого человека и дать ему свой персональный реферальный код.\n\n"
        "📌 <b>Условие:</b> приведенный вами человек должен совершить покупку минимум <b>20 любых монет</b> в нашем боте.\n\n"
        f"🔗 <b>Ваша индивидуальная реферальная ссылка:</b>\n<a href='{ref_link}'>{ref_link}</a>\n\n"
        "Для получения и подтверждения бонусов пишите напрямик: @StarsManagerr"
    )
    keyboard = [
        [InlineKeyboardButton(text="📞 Написать менеджеру", url="https://t.me/StarsManagerr")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    await show_new_screen(callback, "image18.jfif", ref_text, InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data == "faq")
async def show_faq(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    faq_text = (
        "❓ <b>Часто задаваемые вопросы (FAQ)</b>\n\n"
        "Добро пожаловать в справочный центр StarsBiest! Здесь собрана вся ключевая база знаний о нашей платформе, активах, правилах безопасности и принципах работы реферальной программы.\n\n"
        "Мы постарались ответить на все самые популярные вопросы новичков и постоянных клиентов, чтобы вам было максимально комфортно.\n\n"
        "📖 Вы можете подробно <a href='https://1drv.ms/b/c/b68296d9a1b801f9/IQAIvZtAHTAXS6M4J9YeJC5dAQd6XAdgsk1l01p2t4pAaL4'>ознакомиться здесь</a> со всеми материалами в нашем официальном справочном PDF-файле.\n\n"
        "Если у вас останутся дополнительные вопросы, наша команда поддержки всегда на связи!"
    )
    keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    await show_new_screen(callback, "image14.jfif", faq_text, InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.in_({"metis", "agave", "avto", "software"}))
async def show_product(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.data == "metis":
        text = (
            "Metis Coin – оптимистичная монета обеспечивающая безопасность и масштабность протокола.\n"
            "Из-за низкого уровня защиты, с помощью качественного софта BRUT FORCE, можно применять монеты пользователей без их ведома для личных целей.\n\n"
            "📉 Цена одной BRUT монеты - 1450₽\n"
            "📈 Цена монеты на бирже - 3147₽\n\n"
            f"Для заказа, напишите менеджеру : {MANAGER_USERNAME}"
        )
        photo_file = "image16.jfif"
    elif callback.data == "agave":
        text = (
            "Agave Coin — это утилит токен, созданный для упрощения механизма участия инвесторов в развитии индустрии полезных культур.\n"
            "В нем мы обнаружили лазейку в технической части монеты, что позволяет тактически брутить валюту пользователей.\n\n"
            "📉 Цена одной BRUT монеты - 1830₽\n"
            "📈 Цена монеты на бирже - 4237₽\n\n"
            f"Для заказа, напишите менеджеру : {MANAGER_USERNAME}"
        )
        photo_file = "image17.jfif"
    elif callback.data == "avto":
        text = (
            "Avto Coin - это агрегатор урожайного земледелия, работающий как на Binance Smart Chain.\n"
            "Разработчики не сильно заморочились над защитой, поэтому мы нашли способ брутить монеты в средних обьемах.\n\n"
            "📉 Цена одной BRUT монеты - 1055₽\n"
            "📈 Цена монеты на бирже - 1863₽\n\n"
            f"Для заказа, напишите менеджеру : {MANAGER_USERNAME}"
        )
        photo_file = "image15.jfif"
    elif callback.data == "software":
        text = (
            "Персональный софт от команды ✨Stars️\n\n"
            "С нашим софтом вы лично можете заниматься Брутом монет.\n\n"
            "Преимущества софта:\n"
            "- Скорость🚀\n"
            "- Валидность🌟\n"
            "- Легкость✅\n"
            "- Гарантия и полное кураторство🤝\n"
            "- Живая встреча г.Москва по вопросам📱\n\n"
            "Цена: 250$\n\n"
            "📩Для приобретения пишите менеджеру!\n"
            f"👨‍💻 Менеджер: {MANAGER_USERNAME}"
        )
        photo_file = "image19.jfif"

    buy_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить 🛒", callback_data=f"buy_{callback.data}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog")]
    ])
    await show_new_screen(callback, photo_file, text, buy_kb)

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
    await show_new_screen(callback, photo_file, text, buy_kb)

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
    await show_new_screen(callback, "image14.jfif", text, back_kb)

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
        await message.answer_photo(photo=photo, caption=order_card_text, reply_markup=finish_kb, parse_mode="HTML")
    except Exception:
        await message.answer(order_card_text, reply_markup=finish_kb, parse_mode="HTML")

@dp.callback_query(F.data == "guarantees")
async def show_guarantees(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Как оформляется договор?", callback_data="contract_info")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await show_new_screen(callback, "image19.jfif", GUARANTEES_TEXT, kb)

@dp.callback_query(F.data == "contract_info")
async def show_contract_info(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="guarantees")]
    ])
    await show_new_screen(callback, "image19.jfif", CONTRACT_TEXT, kb)

@dp.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user = callback.from_user
    bot_info = await bot.get_me()
    username = f"@{user.username}" if user.username else "Отсутствует"
    ref_code = f"ref_{user.id}"
    ref_link = f"https://t.me/{bot_info.username}?start={ref_code}"
    
    profile_text = (
        "👤 <b>Ваш профиль</b>\n\n"
        f"Username: {username}\n"
        f"ID: {user.id}\n"
        f"Реферальный код: {ref_code}\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n<a href='{ref_link}'>{ref_link}</a>"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await show_new_screen(callback, "image13.jfif", profile_text, back_kb)

# --- ОСНОВНОЙ ЗАПУСК (БОТ + ВЕБ-СЕРВЕР) ---
async def main():
    asyncio.create_task(start_web_server())
    print("Бот запущен и полностью готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
