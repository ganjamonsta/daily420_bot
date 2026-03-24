"""Клавиатуры (inline & reply) — «Вырасти Куст» @daily420_bot."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# ─── Reply‑клавиатура главного меню ──────────────────────────────────

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["💧 Полить", "💡 Свет"],
        ["🌿 Накормить", "🌬️ Проветрить"],
        ["📊 Статус", "📜 Факт"],
        ["🏪 Магазин", "🏆 Лидерборд"],
        ["📤 Похвастаться", "🎮 Мини-игра"],
    ],
    resize_keyboard=True,
)

HARVEST_MENU = ReplyKeyboardMarkup(
    [
        ["🏆 Собрать урожай"],
        ["📊 Статус", "📜 Факт"],
    ],
    resize_keyboard=True,
)

START_MENU = ReplyKeyboardMarkup(
    [["🌱 Начать новый гров"]],
    resize_keyboard=True,
)


# ─── Inline‑клавиатуры ───────────────────────────────────────────────

def cure_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💊 Вылечить", callback_data="cure")],
    ])


def shop_keyboard(items: dict) -> InlineKeyboardMarkup:
    buttons = []
    for key, item in items.items():
        label = f"{item['name']} — {item['price']}💰"
        buttons.append([InlineKeyboardButton(label, callback_data=f"buy:{key}")])
    buttons.append([InlineKeyboardButton("❌ Закрыть", callback_data="close_shop")])
    return InlineKeyboardMarkup(buttons)


def sell_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Продать урожай", callback_data="sell_buds")],
    ])


def share_keyboard(text: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📤 Поделиться",
            switch_inline_query=text,
        )],
    ])


def confirm_harvest_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Собрать урожай!", callback_data="harvest_confirm")],
        [InlineKeyboardButton("⏳ Подожду ещё", callback_data="harvest_wait")],
    ])


def rename_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Переименовать растение", callback_data="rename")],
    ])


def pot_color_keyboard() -> InlineKeyboardMarkup:
    colors = ["🟤", "⚫", "🔴", "🟢", "🔵", "🟡", "🟣", "⚪"]
    rows = []
    row = []
    for c in colors:
        row.append(InlineKeyboardButton(c, callback_data=f"pot:{c}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def minigame_keyboard(options: list[str], correct: str) -> InlineKeyboardMarkup:
    buttons = []
    for opt in options:
        buttons.append([InlineKeyboardButton(opt, callback_data=f"minigame:{opt}")])
    return InlineKeyboardMarkup(buttons)
