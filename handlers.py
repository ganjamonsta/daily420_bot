"""Telegram‑хендлеры — «Вырасти Куст» @daily420_bot.

Лор‑флоу: Дух Древнего Гроубокса встречает игрока,
каждая стадия привязана к культуре.
"""
from __future__ import annotations

import datetime as _dt
import random

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
from game import (
    check_miss_penalty,
    cure_plant,
    do_harvest,
    get_active_plant,
    get_or_create_user,
    get_plant_status,
    perform_action,
    start_new_grow,
)
from keyboards import (
    HARVEST_MENU,
    MAIN_MENU,
    START_MENU,
    confirm_harvest_keyboard,
    cure_keyboard,
    minigame_keyboard,
    pot_color_keyboard,
    rename_keyboard,
    share_keyboard,
    shop_keyboard,
)
from models import Inventory, async_session
from strains import STAGE_INFO, STRAINS, random_phrase
from lore import SPIRIT_INTRO, random_fact, random_fact_for_stage, cultural_phrase

# ═══════════════════════════════════════════════════════════════════════
# Дисклеймеры
# ═══════════════════════════════════════════════════════════════════════

DISCLAIMER = (
    "⚠️ *ДИСКЛЕЙМЕР*\n"
    "Это 100% виртуальная шутка и игра!\n"
    "В России выращивание каннабиса запрещено законом.\n"
    "Не повторяй в реале! 🔥\n"
    "Бот создан исключительно для развлечения.\n"
    "Никакой пропаганды — только мемы и история."
)

DISCLAIMER_SHORT = "⚠️ Это виртуальная шутка! В РФ — запрещено. Не повторяй!"

DISCLAIMER_HARVEST = (
    "⚠️ Помни: это шутка, виртуальная игра.\n"
    "В реальной жизни — не повторяй!\n"
    "Закон суров, а мы тут чисто для прикола. 😉"
)


# ═══════════════════════════════════════════════════════════════════════
# /start — Дух Древнего Гроубокса приветствует
# ═══════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)

        if plant:
            status = get_plant_status(plant, user)
            penalty = check_miss_penalty(plant)
            text = f"У тебя уже растёт куст!\n\n{status}"
            if penalty:
                text = f"{penalty}\n\n{text}"
            kb = HARVEST_MENU if plant.stage == "harvest" else MAIN_MENU
            await update.message.reply_text(text, reply_markup=kb)
            await session.commit()
            return

        plant, strain_data = await start_new_grow(session, user)
        await session.commit()

    origin_emoji = {"himalaya": "🏔️", "silk_road": "🕌", "america": "🇺🇸"}.get(
        strain_data.get("origin", ""), "🌍"
    )

    # Сообщение 1: Лор-вступление Духа
    await update.message.reply_text(
        SPIRIT_INTRO,
        parse_mode="Markdown",
    )

    # Сообщение 2: Дисклеймер
    await update.message.reply_text(
        DISCLAIMER,
        parse_mode="Markdown",
    )

    # Сообщение 3: Семечко
    await update.message.reply_text(
        f"{'─' * 28}\n"
        f"🌰 *Твоё семечко:*\n\n"
        f"{origin_emoji} *{strain_data['name']}*\n"
        f"_{strain_data['desc']}_\n"
        f"Тип: {strain_data['type']} | Родина: {origin_emoji}\n\n"
        f"🏔️ Это семечко зародилось в Гималаях, у храма Шивы.\n"
        f"Впереди — Шёлковый путь, Калифорния и мировой харвест!\n\n"
        f"Ухаживай каждый день:\n"
        f"💧 Полить | 💡 Свет | 🌿 Накормить | 🌬️ Проветрить\n\n"
        f"⚡ У тебя {config.ENERGY_MAX} действия в день.\n"
        f"Удачи, гровер! Дух Древнего Гроубокса с тобой 🔥",
        parse_mode="Markdown",
        reply_markup=MAIN_MENU,
    )


# ═══════════════════════════════════════════════════════════════════════
# /help
# ═══════════════════════════════════════════════════════════════════════

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"📖 *Вырасти Куст — Помощь*\n\n"
        f"*Команды (работают в чатах через /cmd@daily420\\_bot):*\n"
        f"🌱 /start — получить семечко от Духа\n"
        f"📊 /status — посмотреть куст\n"
        f"📜 /fact — исторический факт от Духа\n"
        f"🏪 /shop — магазин за монеты\n"
        f"🏆 /leaderboard — топ гроверов\n"
        f"🎮 /minigame — бонусные монеты\n"
        f"📤 /share — похвастаться кустом\n"
        f"🎨 /customize — кастомизация куста\n"
        f"🔥 /lore — история Духа Гроубокса\n\n"
        f"*Кнопки в личке:*\n"
        f"💧💡🌿🌬️ — действия (4 в день)\n\n"
        f"*Путь роста:*\n"
        f"🏔️ 🌰→🌱 Гималаи (семечко/росток)\n"
        f"🕌 🌿 Шёлковый путь (вегетация)\n"
        f"🇺🇸 🌺 420-Америка (цветение)\n"
        f"🌍 🏆 Мировой харвест!\n\n"
        f"{DISCLAIMER}",
        parse_mode="Markdown",
    )


# ═══════════════════════════════════════════════════════════════════════
# /lore — рассказ Духа о себе
# ═══════════════════════════════════════════════════════════════════════

async def cmd_lore(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"🔥 *История Духа Древнего Гроубокса*\n\n"
        f"*Глава 1 — Гималаи* 🏔️\n"
        f"≈ 2000 лет до н.э. Atharva Veda называет каннабис "
        f"одним из пяти священных растений. Садху у подножия "
        f"Кайласа собирают чарас руками. Шива улыбается.\n\n"
        f"*Глава 2 — Шёлковый Путь* 🕌\n"
        f"VIII–XV века. Караваны несут семена из Центральной Азии "
        f"в Персию, Багдад, Марокко. Суфийские мистики ищут истину. "
        f"Ибн аль-Байтар пишет фармакопею. В горах Рифа рождается киф.\n\n"
        f"*Глава 3 — 420-Америка* 🇺🇸\n"
        f"1971 год, San Rafael High School. Пятеро парней (Waldos) "
        f"встречаются в 4:20 PM у статуи Пастера. Grateful Dead "
        f"разносят код по миру. High Times, Cannabis Cup, легализация.\n\n"
        f"*Глава 4 — Твой телефон* 📱\n"
        f"Сейчас. Дух прошёл весь путь и живёт в @daily420_bot. "
        f"Виртуально, для прикола, с мемами.\n\n"
        f"{DISCLAIMER_SHORT}",
        parse_mode="Markdown",
    )


# ═══════════════════════════════════════════════════════════════════════
# /menu
# ═══════════════════════════════════════════════════════════════════════

async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    async with async_session() as session:
        user = await get_or_create_user(session, update.effective_user.id)
        plant = await get_active_plant(session, user.id)
    kb = MAIN_MENU if plant and plant.stage != "harvest" else (HARVEST_MENU if plant else START_MENU)
    await update.message.reply_text(
        f"📋 *Меню Духа*\n\n{DISCLAIMER}",
        parse_mode="Markdown",
        reply_markup=kb,
    )


# ═══════════════════════════════════════════════════════════════════════
# Действия: полив, свет, кормёжка, проветривание
# ═══════════════════════════════════════════════════════════════════════

ACTION_MAP = {
    "💧 Полить": "water",
    "💡 Свет": "light",
    "🌿 Накормить": "feed",
    "🌬️ Проветрить": "ventilate",
}


async def handle_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    action_key = ACTION_MAP.get(update.message.text)
    if not action_key:
        return

    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)

        if not plant:
            await update.message.reply_text(
                "У тебя нет куста! Жми /start 🌱",
                reply_markup=START_MENU,
            )
            return

        penalty = check_miss_penalty(plant)
        if penalty:
            await update.message.reply_text(penalty)

        result = await perform_action(session, plant, action_key, user)
        await session.commit()

    kb = MAIN_MENU
    if result.get("harvested"):
        kb = HARVEST_MENU
    if result.get("event") and result["event"]["type"] == "problem":
        await update.message.reply_text(
            result["message"], reply_markup=cure_keyboard()
        )
        return
    await update.message.reply_text(result["message"], reply_markup=kb)


# ═══════════════════════════════════════════════════════════════════════
# 📜 Факт — рандомный исторический факт
# ═══════════════════════════════════════════════════════════════════════

async def handle_fact(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)

    if plant:
        fact = random_fact_for_stage(plant.stage)
    else:
        fact = random_fact()

    await update.message.reply_text(
        f"📜 *Дух Древнего Гроубокса рассказывает:*\n\n{fact}\n\n{DISCLAIMER_SHORT}",
        parse_mode="Markdown",
    )


# ═══════════════════════════════════════════════════════════════════════
# Статус
# ═══════════════════════════════════════════════════════════════════════

async def handle_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await update.message.reply_text(
                "Нет активного куста! Жми /start 🌱",
                reply_markup=START_MENU,
            )
            return
        status = get_plant_status(plant, user)
        await session.commit()

    kb = HARVEST_MENU if plant.stage == "harvest" else MAIN_MENU
    await update.message.reply_text(status, reply_markup=kb)


# ═══════════════════════════════════════════════════════════════════════
# Магазин
# ═══════════════════════════════════════════════════════════════════════

async def handle_shop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)

    await update.message.reply_text(
        f"🏪 *Базар Шёлкового пути — Магазин*\n\n"
        f"💰 Твой баланс: {user.coins} монет\n\n"
        f"Выбери товар:",
        parse_mode="Markdown",
        reply_markup=shop_keyboard(config.SHOP_ITEMS),
    )


async def callback_buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    item_key = data.split(":", 1)[1] if ":" in data else ""
    item = config.SHOP_ITEMS.get(item_key)
    if not item:
        await query.edit_message_text("Товар не найден 🤷")
        return

    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id)
        if user.coins < item["price"]:
            await query.edit_message_text(
                f"Не хватает монет! Нужно {item['price']}💰, у тебя {user.coins}💰"
            )
            return

        user.coins -= item["price"]

        existing = None
        for inv in user.inventory:
            if inv.item_key == item_key:
                existing = inv
                break
        if existing:
            existing.quantity += 1
        else:
            new_inv = Inventory(
                user_id=user.id, item_key=item_key, equipped=True
            )
            session.add(new_inv)
        await session.commit()

    await query.edit_message_text(
        f"✅ Куплено: {item['name']}!\n"
        f"💰 Остаток: {user.coins} монет\n"
        f"Дух Древнего Гроубокса одобряет! 🔥"
    )


async def callback_close_shop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🏪 Базар закрыт. Расти дальше, гровер! 🌿")


# ═══════════════════════════════════════════════════════════════════════
# Лечение
# ═══════════════════════════════════════════════════════════════════════

async def callback_cure(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await query.edit_message_text("Нет куста 🤷")
            return
        msg = await cure_plant(session, plant)
        await session.commit()
    await query.edit_message_text(msg)


# ═══════════════════════════════════════════════════════════════════════
# Харвест
# ═══════════════════════════════════════════════════════════════════════

async def handle_harvest_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant or plant.stage != "harvest":
            await update.message.reply_text("Куст ещё не готов! 🌱")
            return

        strain_data = STRAINS.get(plant.strain_key, {})
        strain_name = strain_data.get("name", "???")

    await update.message.reply_text(
        f"🌍🏆 Мировой Харвест *{strain_name}*?\n\n"
        f"🏔️→🕌→🇺🇸→🌍\n"
        f"Дух Древнего Гроубокса готов благословить сбор!\n\n"
        f"{DISCLAIMER_HARVEST}",
        parse_mode="Markdown",
        reply_markup=confirm_harvest_keyboard(),
    )


async def callback_harvest_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await query.edit_message_text("Нет куста 🤷")
            return
        result = await do_harvest(session, plant, user)
        await session.commit()

    await query.edit_message_text(result["message"], parse_mode="Markdown")


async def callback_harvest_wait(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("Окей, пусть дозревает! 🌿")
    await query.edit_message_text("⏳ Дух говорит: терпение — главная добродетель гровера! Подождём.")


# ═══════════════════════════════════════════════════════════════════════
# Начать новый гров
# ═══════════════════════════════════════════════════════════════════════

async def handle_new_grow(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, ctx)


# ═══════════════════════════════════════════════════════════════════════
# Лидерборд
# ═══════════════════════════════════════════════════════════════════════

async def handle_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    from sqlalchemy import select, desc
    from models import HarvestLog, User as UserModel

    async with async_session() as session:
        week_ago = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=7)
        stmt = (
            select(
                HarvestLog.user_id,
                UserModel.username,
                HarvestLog.buds,
                HarvestLog.strain_key,
            )
            .join(UserModel, HarvestLog.user_id == UserModel.id)
            .where(HarvestLog.harvested_at >= week_ago)
            .order_by(desc(HarvestLog.buds))
            .limit(config.LEADERBOARD_SIZE)
        )
        result = await session.execute(stmt)
        rows = result.all()

    if not rows:
        await update.message.reply_text(
            "🏆 Лидерборд Духа пуст!\nБудь первым, кто соберёт мировой харвест!"
        )
        return

    lines = ["🏆 <b>ТОП ГРОВЕРОВ (за неделю)</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i + 1}."
        name = row.username or "Аноним"
        strain = STRAINS.get(row.strain_key, {}).get("name", "???")
        lines.append(f"{medal} @{name} — {row.buds} шишек ({strain})")

    lines.append(f"\n{DISCLAIMER_SHORT}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════════
# Похвастаться
# ═══════════════════════════════════════════════════════════════════════

async def handle_share(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await update.message.reply_text("Нет куста для хвастовства! 🌱")
            return

        strain_data = STRAINS.get(plant.strain_key, {})
        strain_name = strain_data.get("name", "???")
        stage_info = STAGE_INFO.get(plant.stage, STAGE_INFO["seed"])
        origin_emoji = {"himalaya": "🏔️", "silk_road": "🕌", "america": "🇺🇸"}.get(
            strain_data.get("origin", ""), "🌍"
        )

    share_text = (
        f"🌿 Я выращиваю {strain_name} в @daily420_bot!\n"
        f"{origin_emoji} Стадия: {stage_info['emoji']} {stage_info['title']}\n"
        f"Рост: {plant.growth_points:.0f} | Путь: 🏔️→🕌→🇺🇸→🌍\n"
        f"Попробуй — виртуальный прикол от Духа Гроубокса! 🔥"
    )
    await update.message.reply_text(
        f"📤 <b>Похвастайся кустом!</b>\n\n{share_text}",
        parse_mode="HTML",
        reply_markup=share_keyboard(share_text),
    )


# ═══════════════════════════════════════════════════════════════════════
# Кастомизация
# ═══════════════════════════════════════════════════════════════════════

async def cmd_customize(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎨 Кастомизация:\n"
        "✏️ Переименовать куст\n"
        "🪴 Сменить цвет горшка",
        reply_markup=rename_keyboard(),
    )
    await update.message.reply_text("Выбери цвет горшка:", reply_markup=pot_color_keyboard())


async def callback_pot_color(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    color = query.data.split(":", 1)[1] if ":" in query.data else "🟤"
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id)
        plant = await get_active_plant(session, user.id)
        if plant:
            plant.pot_color = color
            await session.commit()
    await query.edit_message_text(f"Горшок изменён на {color}! Дух одобряет.")


async def callback_rename(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✏️ Отправь новое имя для куста (до 30 символов):"
    )
    ctx.user_data["awaiting_rename"] = True


async def handle_rename_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.user_data.get("awaiting_rename"):
        return
    ctx.user_data["awaiting_rename"] = False
    new_name = update.message.text.strip()[:30]
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id)
        plant = await get_active_plant(session, user.id)
        if plant:
            plant.custom_name = new_name
            await session.commit()
    await update.message.reply_text(
        f"✅ Куст переименован в «{new_name}»! 🌿",
        reply_markup=MAIN_MENU,
    )


# ═══════════════════════════════════════════════════════════════════════
# Мини‑игра: вопросы Духа
# ═══════════════════════════════════════════════════════════════════════

MINIGAME_QUESTIONS = [
    {
        "q": "🏔️ Какой лайт‑цикл запускает цветение?",
        "options": ["18/6", "20/4", "12/12", "24/0"],
        "answer": "12/12",
    },
    {
        "q": "🕌 Сколько часов света нужно на вегетации?",
        "options": ["8", "12", "18", "6"],
        "answer": "18",
    },
    {
        "q": "🇺🇸 Waldos встречались в 4:20 PM. Какой это год?",
        "options": ["1965", "1971", "1979", "1984"],
        "answer": "1971",
    },
    {
        "q": "🏔️ Какой pH воды оптимален для почвы?",
        "options": ["4.5", "5.5", "6.5", "8.0"],
        "answer": "6.5",
    },
    {
        "q": "🕌 Из какой страны родом сорт \"Марокканский Киф\"?",
        "options": ["Иран", "Марокко", "Египет", "Ливан"],
        "answer": "Марокко",
    },
    {
        "q": "🇺🇸 Какой штат первым легализовал рекреационку?",
        "options": ["Калифорния", "Колорадо", "Орегон", "Невада"],
        "answer": "Колорадо",
    },
    {
        "q": "🏔️ Что такое чарас?",
        "options": ["Сорт чая", "Ручной гашиш", "Вид удобрения", "Горный цветок"],
        "answer": "Ручной гашиш",
    },
    {
        "q": "🌍 Какой газ растение поглощает при фотосинтезе?",
        "options": ["O₂", "N₂", "CO₂", "H₂"],
        "answer": "CO₂",
    },
]


async def handle_minigame(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = random.choice(MINIGAME_QUESTIONS)
    options = list(q["options"])
    random.shuffle(options)
    ctx.user_data["minigame_answer"] = q["answer"]
    await update.message.reply_text(
        f"🎮 <b>Мини‑игра Духа!</b>\n\n"
        f"{q['q']}\n"
        f"(Дух загадал вопрос из мирового учебника 🌍)",
        parse_mode="HTML",
        reply_markup=minigame_keyboard(options, q["answer"]),
    )


async def callback_minigame(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    answer = query.data.split(":", 1)[1] if ":" in query.data else ""
    correct = ctx.user_data.get("minigame_answer", "12/12")

    if answer == correct:
        tg = update.effective_user
        bonus = 5
        async with async_session() as session:
            user = await get_or_create_user(session, tg.id)
            user.coins += bonus
            await session.commit()
        await query.edit_message_text(
            f"🎉 Правильно! {correct}!\n+{bonus} монет 💰\n"
            f"Дух Древнего Гроубокса впечатлён!"
        )
    else:
        await query.edit_message_text(
            f"❌ Неправильно! Ответ: {correct}\n"
            f"Дух говорит: «Учись, молодой гровер!» 📚"
        )


# ═══════════════════════════════════════════════════════════════════════
# Регистрация хендлеров
# ═══════════════════════════════════════════════════════════════════════

def register_handlers(app: Application) -> None:
    # Команды (работают и в группах через /cmd@daily420_bot)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("lore", cmd_lore))
    app.add_handler(CommandHandler("customize", cmd_customize))
    app.add_handler(CommandHandler("minigame", handle_minigame))
    app.add_handler(CommandHandler("fact", handle_fact))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("shop", handle_shop))
    app.add_handler(CommandHandler("leaderboard", handle_leaderboard))
    app.add_handler(CommandHandler("share", handle_share))

    # Действия (reply‑кнопки)
    app.add_handler(MessageHandler(
        filters.Text(list(ACTION_MAP.keys())), handle_action
    ))
    app.add_handler(MessageHandler(filters.Text(["📊 Статус"]), handle_status))
    app.add_handler(MessageHandler(filters.Text(["📜 Факт"]), handle_fact))
    app.add_handler(MessageHandler(filters.Text(["🏪 Магазин"]), handle_shop))
    app.add_handler(MessageHandler(filters.Text(["🏆 Лидерборд"]), handle_leaderboard))
    app.add_handler(MessageHandler(filters.Text(["📤 Похвастаться"]), handle_share))
    app.add_handler(MessageHandler(filters.Text(["🎮 Мини-игра"]), handle_minigame))
    app.add_handler(MessageHandler(
        filters.Text(["🏆 Собрать урожай"]), handle_harvest_button
    ))
    app.add_handler(MessageHandler(
        filters.Text(["🌱 Начать новый гров"]), handle_new_grow
    ))

    # Callback‑query (inline‑кнопки)
    app.add_handler(CallbackQueryHandler(callback_buy, pattern=r"^buy:"))
    app.add_handler(CallbackQueryHandler(callback_close_shop, pattern=r"^close_shop$"))
    app.add_handler(CallbackQueryHandler(callback_cure, pattern=r"^cure$"))
    app.add_handler(CallbackQueryHandler(callback_harvest_confirm, pattern=r"^harvest_confirm$"))
    app.add_handler(CallbackQueryHandler(callback_harvest_wait, pattern=r"^harvest_wait$"))
    app.add_handler(CallbackQueryHandler(callback_pot_color, pattern=r"^pot:"))
    app.add_handler(CallbackQueryHandler(callback_rename, pattern=r"^rename$"))
    app.add_handler(CallbackQueryHandler(callback_minigame, pattern=r"^minigame:"))

    # Текст (переименование) — последний, как fallback
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_rename_text
    ))
