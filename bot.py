
import asyncio
import json
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, BotCommand,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)

TOKEN = os.environ["BOT_TOKEN"]
SITE = "https://hongguoduanju.com/"
DATA = Path(__file__).with_name("dramas.json")

bot = Bot(token=TOKEN)
dp = Dispatcher()
languages = {}
searching = set()

WELCOME = {
    "en": "🎬 Welcome to AI Drama Hub!\nExplore short dramas and find something to watch.",
    "hi": "🎬 AI Drama Hub में आपका स्वागत है!\nशॉर्ट ड्रामा खोजें और देखें।",
    "pt": "🎬 Bem-vindo ao AI Drama Hub!\nExplore minidramas e encontre o que assistir.",
    "vi": "🎬 Chào mừng đến với AI Drama Hub!\nKhám phá và tìm phim ngắn để xem.",
    "id": "🎬 Selamat datang di AI Drama Hub!\nJelajahi dan cari drama pendek untuk ditonton.",
    "zh": "🎬 欢迎来到 AI Drama Hub！\n探索精彩短剧，寻找你喜欢的作品。"
}

LANG_NAMES = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिन्दी",
    "pt": "🇧🇷 Português",
    "vi": "🇻🇳 Tiếng Việt",
    "id": "🇮🇩 Bahasa Indonesia",
    "zh": "🇨🇳 中文"
}

def lang(user):
    saved = languages.get(user.id)
    if saved:
        return saved
    code = (user.language_code or "en").split("-")[0].lower()
    return code if code in WELCOME else "en"

def dramas():
    return json.loads(DATA.read_text(encoding="utf-8"))

def main_menu():
    rows = [
        [
            InlineKeyboardButton(text="🔎 Search", callback_data="search"),
            InlineKeyboardButton(text="🎭 Categories", callback_data="categories")
        ],
        [
            InlineKeyboardButton(text="🔥 Popular", callback_data="popular"),
            InlineKeyboardButton(text="✨ AI Dramas", callback_data="ai")
        ],
        [
            InlineKeyboardButton(text="🌍 Language", callback_data="language"),
            InlineKeyboardButton(text="❓ Help", callback_data="help")
        ],
        [
            InlineKeyboardButton(
                text="🎬 Watch Dramas",
                web_app=WebAppInfo(url=SITE)
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def drama_buttons(items):
    rows = []
    for item in items[:10]:
        rows.append([
            InlineKeyboardButton(
                text=f"🎬 {item['title'][:40]}",
                callback_data=f"drama:{item['id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def show_list(message, items, title):
    if not items:
        await message.answer(
            f"{title}\n\nNo dramas available in this section yet."
        )
        return
    await message.answer(title, reply_markup=drama_buttons(items))

@dp.message(Command("start"))
async def start(message: Message):
    searching.discard(message.from_user.id)
    await message.answer(
        WELCOME[lang(message.from_user)],
        reply_markup=main_menu()
    )

@dp.message(Command("watch"))
async def watch(message: Message):
    await message.answer("🎬 Open the drama website:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="▶️ Watch Dramas",
                web_app=WebAppInfo(url=SITE)
            )
        ]]))

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "Search for dramas by title, browse categories, "
        "or explore our available collection.\n"
        "Use /language to change the bot language.\n"
        "The external website may have different language options.",
        reply_markup=main_menu()
    )

@dp.message(Command("search"))
async def search_cmd(message: Message):
    searching.add(message.from_user.id)
    await message.answer("🔎 Send a drama title or keyword.")

@dp.message(Command("categories"))
async def categories_cmd(message: Message):
    await show_categories(message)

async def show_categories(message):
    categories = sorted({
        d["category"] for d in dramas() if d.get("category")
    })
    if not categories:
        await message.answer("No categories available yet.")
        return
    rows = [
        [InlineKeyboardButton(text=c, callback_data=f"cat:{i}")]
        for i, c in enumerate(categories)
    ]
    await message.answer(
        "🎭 Select a category:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.message(Command("popular"))
async def popular_cmd(message: Message):
    await show_list(
        message,
        [d for d in dramas() if d.get("popular")],
        "🔥 Popular Dramas"
    )

@dp.message(Command("ai"))
async def ai_cmd(message: Message):
    await show_list(
        message,
        [d for d in dramas() if d.get("ai")],
        "✨ AI Dramas"
    )

@dp.message(Command("language"))
async def language_cmd(message: Message):
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"lang:{code}")]
        for code, name in LANG_NAMES.items()
    ]
    await message.answer(
        "🌍 Choose your language:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query(F.data == "search")
async def search_btn(call: CallbackQuery):
    await call.answer()
    await search_cmd(call.message_with_user if False else
                     _message_proxy(call))

class _message_proxy:
    def __init__(self, call):
        self.from_user = call.from_user
        self.answer = call.message.answer

@dp.callback_query(F.data == "categories")
async def categories_btn(call: CallbackQuery):
    await call.answer()
    await show_categories(call.message)

@dp.callback_query(F.data == "popular")
async def popular_btn(call: CallbackQuery):
    await call.answer()
    await show_list(
        call.message,
        [d for d in dramas() if d.get("popular")],
        "🔥 Popular Dramas"
    )

@dp.callback_query(F.data == "ai")
async def ai_btn(call: CallbackQuery):
    await call.answer()
    await show_list(
        call.message,
        [d for d in dramas() if d.get("ai")],
        "✨ AI Dramas"
    )

@dp.callback_query(F.data == "help")
async def help_btn(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        "Use Search, Categories or Popular to discover dramas."
    )

@dp.callback_query(F.data == "language")
async def language_btn(call: CallbackQuery):
    await call.answer()
    rows = [
        [InlineKeyboardButton(text=n, callback_data=f"lang:{c}")]
        for c, n in LANG_NAMES.items()
    ]
    await call.message.answer(
        "Choose your language:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query(F.data.startswith("lang:"))
async def set_language(call: CallbackQuery):
    await call.answer()
    code = call.data.split(":", 1)[1]
    if code not in LANG_NAMES:
        return
    languages[call.from_user.id] = code
    await call.message.answer(
        WELCOME[code], reply_markup=main_menu()
    )

@dp.callback_query(F.data.startswith("cat:"))
async def category_btn(call: CallbackQuery):
    await call.answer()
    categories = sorted({
        d["category"] for d in dramas() if d.get("category")
    })
    try:
        category = categories[int(call.data.split(":")[1])]
    except (ValueError, IndexError):
        await call.message.answer("Category not found.")
        return
    await show_list(
        call.message,
        [d for d in dramas() if d.get("category") == category],
        f"🎭 {category}"
    )

@dp.callback_query(F.data.startswith("drama:"))
async def drama_btn(call: CallbackQuery):
    await call.answer()
    drama_id = call.data.split(":", 1)[1]
    item = next(
        (d for d in dramas() if d["id"] == drama_id), None
    )
    if not item:
        await call.message.answer("Drama not found.")
        return

    await call.message.answer(
        f"🎬 {item['title']}\n\n"
        f"Category: {item.get('category', 'Drama')}\n"
        f"{item.get('description', '')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="▶️ View Drama",
                url=item["url"]
            )
        ]])
    )

@dp.message(F.text)
async def text_handler(message: Message):
    if message.from_user.id not in searching:
        await message.answer(
            "Choose an option from the menu.",
            reply_markup=main_menu()
        )
        return

    keyword = message.text.strip().casefold()
    if not keyword:
        await message.answer("Enter a title.")
        return
    results = [
        d for d in dramas()
        if keyword in d["title"].casefold()
        or keyword in d.get("description", "").casefold()
    ]
    searching.discard(message.from_user.id)
    await show_list(message, results, "🔎 Search Results")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command="start", description="Main menu"),
        BotCommand(command="search", description="Search dramas"),
        BotCommand(command="categories", description="Browse categories"),
        BotCommand(command="popular", description="Popular dramas"),
        BotCommand(command="ai", description="AI dramas"),
        BotCommand(command="watch", description="Watch dramas"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="help", description="Help")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
