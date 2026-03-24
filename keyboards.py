"""Клавиатуры (inline & reply) — «Вырасти Куст» @daily420_bot."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

import config

# ═══════════════════════════════════════════════════════════════════════
# Reply‑клавиатуры (PM, быстрые кнопки)
# ═══════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════
# Старые inline-клавиатуры (совместимость)
# ═══════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════
# Inline-меню с динамическими данными (m: prefix)
# ═══════════════════════════════════════════════════════════════════════

_B = InlineKeyboardButton  # shorthand


def _energy_icon(e: int) -> str:
    if e <= 0:
        return "❌"
    return f"⚡{e}"


def hub_kb(
    energy: int, max_energy: int, coins: int,
    stage: str, is_sick: bool = False,
) -> InlineKeyboardMarkup:
    """Главный хаб — динамические кнопки действий + навигация."""
    ei = _energy_icon(energy)
    rows: list[list[InlineKeyboardButton]] = []

    if stage == "harvest":
        rows.append([_B(f"🏆 Собрать урожай!", callback_data="m:harv")])
    elif is_sick:
        rows.append([_B("💊 Вылечить куст!", callback_data="m:cure")])
    else:
        rows.append([
            _B(f"💧 {ei}", callback_data="m:w"),
            _B(f"💡 {ei}", callback_data="m:l"),
            _B(f"🌿 {ei}", callback_data="m:f"),
            _B(f"🌬 {ei}", callback_data="m:v"),
        ])

    rows.append([
        _B("📊 Статус", callback_data="m:st"),
        _B("📜 Факт", callback_data="m:fact"),
    ])
    rows.append([
        _B(f"🏪 Базар 💰{coins}", callback_data="m:shop"),
        _B("🏆 Топ", callback_data="m:top"),
    ])
    rows.append([
        _B("🎮 Игра", callback_data="m:game"),
        _B("🔥 Лор", callback_data="m:lore"),
    ])
    rows.append([
        _B("📤 Хвастать", callback_data="m:share"),
        _B("🎨 Кастом", callback_data="m:cust"),
    ])
    return InlineKeyboardMarkup(rows)


def no_plant_kb() -> InlineKeyboardMarkup:
    """Кнопка для начала нового грова."""
    return InlineKeyboardMarkup([
        [_B("🌱 Получить семечко!", callback_data="m:newgrow")],
    ])


def back_kb() -> InlineKeyboardMarkup:
    """Одна кнопка «Назад»."""
    return InlineKeyboardMarkup([
        [_B("🔙 Назад", callback_data="m:hub")],
    ])


def status_kb(stage: str) -> InlineKeyboardMarkup:
    """Кнопки статуса: назад в хаб (+ харвест если готов)."""
    rows: list[list[InlineKeyboardButton]] = []
    if stage == "harvest":
        rows.append([_B("🏆 Собрать урожай!", callback_data="m:harv")])
    rows.append([_B("🔙 Назад", callback_data="m:hub")])
    return InlineKeyboardMarkup(rows)


def shop_inline_kb(items: dict, coins: int) -> InlineKeyboardMarkup:
    """Магазин с ценами и индикатором доступности."""
    rows: list[list[InlineKeyboardButton]] = []
    for key, item in items.items():
        can = "✅" if coins >= item["price"] else "🔒"
        label = f"{can} {item['name']} — {item['price']}💰"
        rows.append([_B(label, callback_data=f"m:buy:{key}")])
    rows.append([_B("🔙 Назад", callback_data="m:hub")])
    return InlineKeyboardMarkup(rows)


def lore_chapters_kb() -> InlineKeyboardMarkup:
    """Навигация по главам лора."""
    return InlineKeyboardMarkup([
        [_B("🏔️ Глава 1: Гималаи", callback_data="m:lr:1")],
        [_B("🕌 Глава 2: Шёлковый путь", callback_data="m:lr:2")],
        [_B("🇺🇸 Глава 3: 420-Америка", callback_data="m:lr:3")],
        [_B("📱 Глава 4: Твой телефон", callback_data="m:lr:4")],
        [_B("🔙 Назад", callback_data="m:hub")],
    ])


def lore_chapter_kb(chapter: int) -> InlineKeyboardMarkup:
    """Назад к списку глав / в хаб."""
    btns = []
    if chapter > 1:
        btns.append(_B("⬅️", callback_data=f"m:lr:{chapter - 1}"))
    btns.append(_B("📜 Главы", callback_data="m:lore"))
    if chapter < 4:
        btns.append(_B("➡️", callback_data=f"m:lr:{chapter + 1}"))
    return InlineKeyboardMarkup([
        btns,
        [_B("🔙 Хаб", callback_data="m:hub")],
    ])


def game_question_kb(options: list[str]) -> InlineKeyboardMarkup:
    """Кнопки мини-игры (m: prefix)."""
    rows = []
    # 2 кнопки в ряд
    for i in range(0, len(options), 2):
        row = [_B(options[i], callback_data=f"m:mg:{options[i]}")]
        if i + 1 < len(options):
            row.append(_B(options[i + 1], callback_data=f"m:mg:{options[i + 1]}"))
        rows.append(row)
    rows.append([_B("🔙 Назад", callback_data="m:hub")])
    return InlineKeyboardMarkup(rows)


def game_result_kb() -> InlineKeyboardMarkup:
    """После мини-игры: ещё раз + назад."""
    return InlineKeyboardMarkup([
        [_B("🎮 Ещё раз", callback_data="m:game")],
        [_B("🔙 Назад", callback_data="m:hub")],
    ])


def harvest_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_B("✅ Собрать урожай!", callback_data="m:hc")],
        [_B("⏳ Подожду ещё", callback_data="m:hub")],
    ])


def after_harvest_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_B("🌱 Новый гров!", callback_data="m:newgrow")],
    ])


def customize_kb() -> InlineKeyboardMarkup:
    """Кастомизация куста."""
    colors = ["🟤", "⚫", "🔴", "🟢", "🔵", "🟡", "🟣", "⚪"]
    rows: list[list[InlineKeyboardButton]] = [
        [_B("✏️ Переименовать", callback_data="m:ren")],
    ]
    row: list[InlineKeyboardButton] = []
    for c in colors:
        row.append(_B(c, callback_data=f"m:pot:{c}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([_B("🔙 Назад", callback_data="m:hub")])
    return InlineKeyboardMarkup(rows)


def top_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_B("🔄 Обновить", callback_data="m:top")],
        [_B("🔙 Назад", callback_data="m:hub")],
    ])


def fact_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_B("📜 Ещё факт", callback_data="m:fact")],
        [_B("🔙 Назад", callback_data="m:hub")],
    ])


def share_inline_kb(text: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_B("📤 Поделиться", switch_inline_query=text)],
        [_B("🔙 Назад", callback_data="m:hub")],
    ])
