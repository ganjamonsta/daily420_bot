"""Telegram‑хендлеры — «Вырасти Куст» @daily420_bot.

Лор‑флоу: Дух Древнего Гроубокса встречает игрока,
каждая стадия привязана к культуре.
"""
from __future__ import annotations

import datetime as _dt
import random

from telegram import InputMediaPhoto, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.core import config
from app.gameplay.game import (
    check_miss_penalty,
    cure_plant,
    do_harvest,
    get_active_plant,
    get_or_create_user,
    get_plant_status,
    perform_action,
    start_new_grow,
)
from app.ui.keyboards import (
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
    # Inline-меню
    after_harvest_kb,
    back_kb,
    customize_kb,
    fact_kb,
    game_question_kb,
    game_result_kb,
    harvest_confirm_kb,
    hub_kb,
    lore_chapter_kb,
    lore_chapters_kb,
    no_plant_kb,
    share_inline_kb,
    shop_inline_kb,
    status_kb,
    top_kb,
)
from app.db.models import Inventory, async_session
from app.gameplay.strains import STAGE_INFO, STRAINS, random_phrase
from app.gameplay.lore import SPIRIT_INTRO, random_fact, random_fact_for_stage, cultural_phrase
from app.gameplay import images as img

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
    await cmd_menu_inline(update, ctx)


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
    from app.db.models import HarvestLog, User as UserModel

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
# INLINE MENU SYSTEM  (m: prefix)
# Картинки + инлайн-кнопки + навигация между экранами
# ═══════════════════════════════════════════════════════════════════════

# ─── Helpers ──────────────────────────────────────────────────────────

def _progress(plant) -> float:
    """Прогресс роста 0.0–1.0 по текущей стадии."""
    stages = list(config.STAGES.items())
    for stage_key, (lo, hi) in stages:
        if stage_key == plant.stage:
            if hi is None:
                return 1.0
            span = hi - lo
            return min((plant.growth_points - lo) / span, 1.0) if span > 0 else 1.0
    return 0.0


def _origin_emoji(strain_data: dict) -> str:
    return {"himalaya": "🏔️", "silk_road": "🕌", "america": "🇺🇸"}.get(
        strain_data.get("origin", ""), "🌍")


async def _send_screen(message, photo, caption, kb):
    """Отправить новый экран (photo или text)."""
    if photo:
        return await message.reply_photo(
            photo=photo, caption=caption,
            parse_mode="HTML", reply_markup=kb,
        )
    return await message.reply_text(
        caption, parse_mode="HTML", reply_markup=kb,
    )


async def _edit_screen(query, photo, caption, kb):
    """Обновить существующий экран (photo → edit_media, else edit_text)."""
    try:
        if photo:
            media = InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML")
            await query.edit_message_media(media=media, reply_markup=kb)
        else:
            await query.edit_message_text(
                text=caption, parse_mode="HTML", reply_markup=kb,
            )
    except Exception:
        # Fallback: если не можем отредактировать (переход photo↔text)
        try:
            await query.edit_message_text(
                text=caption, parse_mode="HTML", reply_markup=kb,
            )
        except Exception:
            pass


# ─── /menu — вход в inline-хаб ───────────────────────────────────────

async def cmd_menu_inline(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет inline-хаб с картинкой."""
    tg = update.effective_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)

        if not plant:
            photo = img.no_plant_card()
            caption = "🌿 <b>ВЫРАСТИ КУСТ</b>\n\nУ тебя нет куста!\nЖми кнопку ниже 🌱"
            await _send_screen(update.message, photo, caption, no_plant_kb())
            return

        strain_data = STRAINS.get(plant.strain_key, {})
        stage_info = STAGE_INFO.get(plant.stage, STAGE_INFO["seed"])
        oe = _origin_emoji(strain_data)
        progress = _progress(plant)
        from app.gameplay.game import _maybe_reset_energy
        _maybe_reset_energy(plant)
        await session.commit()

    photo = img.hub_card(
        strain_name=strain_data.get("name", "???"),
        stage_title=stage_info["title"],
        origin=strain_data.get("origin", ""),
        energy=plant.energy, max_energy=config.ENERGY_MAX,
        coins=user.coins, progress=progress, stage=plant.stage,
    )
    caption = (
        f"🌿 <b>ВЫРАСТИ КУСТ</b>\n\n"
        f"{oe} {strain_data.get('name', '???')}\n"
        f"{stage_info['emoji']} {stage_info['title']}"
        f"  {stage_info.get('culture_emoji', '')}\n"
        f"📊 Рост: {plant.growth_points:.0f}  |  "
        f"⚡ {plant.energy}/{config.ENERGY_MAX}  |  💰 {user.coins}"
    )
    kb = hub_kb(plant.energy, config.ENERGY_MAX, user.coins, plant.stage, plant.is_sick)
    await _send_screen(update.message, photo, caption, kb)


# ─── Callback: HUB ───────────────────────────────────────────────────

async def _cb_hub(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant:
            photo = img.no_plant_card()
            caption = "🌿 <b>ВЫРАСТИ КУСТ</b>\n\nУ тебя нет куста!\nЖми кнопку ниже 🌱"
            await _edit_screen(query, photo, caption, no_plant_kb())
            return
        strain_data = STRAINS.get(plant.strain_key, {})
        stage_info = STAGE_INFO.get(plant.stage, STAGE_INFO["seed"])
        oe = _origin_emoji(strain_data)
        progress = _progress(plant)
        from app.gameplay.game import _maybe_reset_energy
        _maybe_reset_energy(plant)
        await session.commit()

    photo = img.hub_card(
        strain_name=strain_data.get("name", "???"),
        stage_title=stage_info["title"],
        origin=strain_data.get("origin", ""),
        energy=plant.energy, max_energy=config.ENERGY_MAX,
        coins=user.coins, progress=progress, stage=plant.stage,
    )
    caption = (
        f"🌿 <b>ВЫРАСТИ КУСТ</b>\n\n"
        f"{oe} {strain_data.get('name', '???')}\n"
        f"{stage_info['emoji']} {stage_info['title']}"
        f"  {stage_info.get('culture_emoji', '')}\n"
        f"📊 Рост: {plant.growth_points:.0f}  |  "
        f"⚡ {plant.energy}/{config.ENERGY_MAX}  |  💰 {user.coins}"
    )
    kb = hub_kb(plant.energy, config.ENERGY_MAX, user.coins, plant.stage, plant.is_sick)
    await _edit_screen(query, photo, caption, kb)


# ─── Callback: ACTION ────────────────────────────────────────────────

_MENU_ACTION_MAP = {"m:w": "water", "m:l": "light", "m:f": "feed", "m:v": "ventilate"}

async def _cb_action(query, ctx, action_key: str) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await _edit_screen(query, img.no_plant_card(),
                               "Нет куста! Жми /start 🌱", no_plant_kb())
            return
        result = await perform_action(session, plant, action_key, user)
        await session.commit()

        if not result["ok"]:
            await _edit_screen(query, None, result["message"], back_kb())
            return

        strain_data = STRAINS.get(plant.strain_key, {})
        stage_info = STAGE_INFO.get(plant.stage, STAGE_INFO["seed"])
        oe = _origin_emoji(strain_data)
        progress = _progress(plant)

    photo = img.hub_card(
        strain_name=strain_data.get("name", "???"),
        stage_title=stage_info["title"],
        origin=strain_data.get("origin", ""),
        energy=plant.energy, max_energy=config.ENERGY_MAX,
        coins=user.coins, progress=progress, stage=plant.stage,
    )
    # Короткий результат действия + обновлённый хаб
    caption = (
        f"{result['message'][:800]}"
    )
    kb = hub_kb(plant.energy, config.ENERGY_MAX, user.coins, plant.stage, plant.is_sick)
    await _edit_screen(query, photo, caption, kb)


# ─── Callback: STATUS ────────────────────────────────────────────────

async def _cb_status(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await _edit_screen(query, img.no_plant_card(),
                               "Нет куста! Жми /start 🌱", no_plant_kb())
            return
        status_text = get_plant_status(plant, user)
        strain_data = STRAINS.get(plant.strain_key, {})
        stage_info = STAGE_INFO.get(plant.stage, STAGE_INFO["seed"])
        progress = _progress(plant)
        days = (_dt.datetime.now(_dt.timezone.utc) -
                plant.started_at.replace(tzinfo=_dt.timezone.utc)).days
        health = "🤒 Болеет" if plant.is_sick else "💚 Здоров"
        await session.commit()

    photo = img.status_card(
        strain_name=strain_data.get("name", "???"),
        stage_title=stage_info["title"],
        origin=strain_data.get("origin", ""),
        energy=plant.energy, max_energy=config.ENERGY_MAX,
        coins=user.coins, growth=plant.growth_points,
        day=days, health=health.replace("🤒 ", "").replace("💚 ", ""),
        progress=progress, stage=plant.stage,
    )
    caption = status_text[:1024]
    await _edit_screen(query, photo, caption, status_kb(plant.stage))


# ─── Callback: FACT ──────────────────────────────────────────────────

async def _cb_fact(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)

    fact = random_fact_for_stage(plant.stage) if plant else random_fact()
    culture = ""
    if plant:
        sd = STRAINS.get(plant.strain_key, {})
        culture = sd.get("origin", "")

    photo = img.fact_card(culture)
    caption = (
        f"📜 <b>Дух Древнего Гроубокса рассказывает:</b>\n\n{fact}\n\n{DISCLAIMER_SHORT}"
    )
    await _edit_screen(query, photo, caption, fact_kb())


# ─── Callback: SHOP ──────────────────────────────────────────────────

async def _cb_shop(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)

    photo = img.shop_card(user.coins)
    caption = (
        f"🏪 <b>БАЗАР ШЁЛКОВОГО ПУТИ</b>\n\n"
        f"💰 Баланс: {user.coins} монет\n"
        f"Выбери товар:"
    )
    await _edit_screen(query, photo, caption, shop_inline_kb(config.SHOP_ITEMS, user.coins))


async def _cb_buy(query, ctx, item_key: str) -> None:
    item = config.SHOP_ITEMS.get(item_key)
    if not item:
        await query.answer("Товар не найден 🤷")
        return

    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id)
        if user.coins < item["price"]:
            await query.answer(
                f"Не хватает! Нужно {item['price']}💰, у тебя {user.coins}💰", show_alert=True
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
            session.add(Inventory(user_id=user.id, item_key=item_key, equipped=True))
        await session.commit()
        coins_left = user.coins

    await query.answer(f"✅ {item['name']} куплено! 💰{coins_left}")
    # Обновляем экран магазина
    photo = img.shop_card(coins_left)
    caption = (
        f"🏪 <b>БАЗАР ШЁЛКОВОГО ПУТИ</b>\n\n"
        f"✅ Куплено: {item['name']}!\n"
        f"💰 Остаток: {coins_left} монет"
    )
    await _edit_screen(query, photo, caption, shop_inline_kb(config.SHOP_ITEMS, coins_left))


# ─── Callback: LEADERBOARD ───────────────────────────────────────────

async def _cb_top(query, ctx) -> None:
    from sqlalchemy import select, desc
    from app.db.models import HarvestLog, User as UserModel

    async with async_session() as session:
        week_ago = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=7)
        stmt = (
            select(HarvestLog.user_id, UserModel.username, HarvestLog.buds, HarvestLog.strain_key)
            .join(UserModel, HarvestLog.user_id == UserModel.id)
            .where(HarvestLog.harvested_at >= week_ago)
            .order_by(desc(HarvestLog.buds))
            .limit(config.LEADERBOARD_SIZE)
        )
        result = await session.execute(stmt)
        rows = result.all()

    photo = img.top_card()
    if not rows:
        caption = "🏆 <b>ТОП ГРОВЕРОВ</b>\n\nПока пусто! Будь первым!"
    else:
        medals = ["🥇", "🥈", "🥉"]
        lines = ["🏆 <b>ТОП ГРОВЕРОВ (за неделю)</b>\n"]
        for i, row in enumerate(rows):
            medal = medals[i] if i < 3 else f"{i + 1}."
            name = row.username or "Аноним"
            strain = STRAINS.get(row.strain_key, {}).get("name", "???")
            lines.append(f"{medal} @{name} — {row.buds} шишек ({strain})")
        lines.append(f"\n{DISCLAIMER_SHORT}")
        caption = "\n".join(lines)
    await _edit_screen(query, photo, caption[:1024], top_kb())


# ─── Callback: LORE ──────────────────────────────────────────────────

LORE_CHAPTERS = {
    1: (
        "🏔️ <b>Глава 1 — Гималаи</b>\n\n"
        "≈ 2000 лет до н.э. Atharva Veda называет каннабис "
        "одним из пяти священных растений.\n\n"
        "Садху у подножия Кайласа собирают чарас руками. "
        "Непальские долины, утренний туман, мантры.\n\n"
        "Шива улыбается. 🙏"
    ),
    2: (
        "🕌 <b>Глава 2 — Шёлковый Путь</b>\n\n"
        "VIII–XV века. Караваны несут семена из Центральной Азии "
        "в Персию, Багдад, Марокко.\n\n"
        "Суфийские мистики ищут истину. Ибн аль-Байтар пишет "
        "фармакопею. В горах Рифа рождается киф. 🐪"
    ),
    3: (
        "🇺🇸 <b>Глава 3 — 420-Америка</b>\n\n"
        "1971, San Rafael High School. Waldos встречаются "
        "в 4:20 PM у статуи Пастера.\n\n"
        "Grateful Dead разносят код по миру. "
        "High Times, Cannabis Cup, легализация. ✌️"
    ),
    4: (
        "📱 <b>Глава 4 — Твой телефон</b>\n\n"
        "Сейчас. Дух прошёл весь путь от Гималаев "
        "через Шёлковый путь до 420-Калифорнии.\n\n"
        "Теперь он живёт в @daily420_bot. "
        "Виртуально, для прикола, с мемами. 🔥"
    ),
}


async def _cb_lore(query, ctx) -> None:
    photo = img.lore_card()
    caption = (
        "🔥 <b>ИСТОРИЯ ДУХА ДРЕВНЕГО ГРОУБОКСА</b>\n\n"
        "Выбери главу:"
    )
    await _edit_screen(query, photo, caption, lore_chapters_kb())


async def _cb_lore_chapter(query, ctx, chapter: int) -> None:
    text = LORE_CHAPTERS.get(chapter, "???")
    palettes = {1: "himalaya", 2: "silk_road", 3: "america", 4: "world"}
    pal = palettes.get(chapter, "lore")
    photo = img.make_card(
        title=f"ГЛАВА {chapter}",
        body_lines=[["Гималаи", "Шёлковый путь", "420-Америка", "Твой телефон"][chapter - 1]],
        palette=pal,
    )
    await _edit_screen(query, photo, f"{text}\n\n{DISCLAIMER_SHORT}", lore_chapter_kb(chapter))


# ─── Callback: MINIGAME ──────────────────────────────────────────────

async def _cb_game(query, ctx) -> None:
    q = random.choice(MINIGAME_QUESTIONS)
    options = list(q["options"])
    random.shuffle(options)
    ctx.user_data["m_game_answer"] = q["answer"]
    photo = img.game_card()
    caption = (
        f"🎮 <b>МИНИ-ИГРА ДУХА</b>\n\n{q['q']}"
    )
    await _edit_screen(query, photo, caption, game_question_kb(options))


async def _cb_game_answer(query, ctx, answer: str) -> None:
    correct = ctx.user_data.get("m_game_answer", "12/12")
    if answer == correct:
        tg = query.from_user
        bonus = 5
        async with async_session() as session:
            user = await get_or_create_user(session, tg.id)
            user.coins += bonus
            await session.commit()
        caption = (
            f"🎉 <b>Правильно!</b> {correct}\n"
            f"+{bonus} монет 💰\n\n"
            f"Дух Древнего Гроубокса впечатлён!"
        )
    else:
        caption = (
            f"❌ <b>Неправильно!</b>\n"
            f"Ответ: {correct}\n\n"
            f"Дух говорит: «Учись, молодой гровер!» 📚"
        )
    photo = img.game_card()
    await _edit_screen(query, photo, caption, game_result_kb())


# ─── Callback: HARVEST ───────────────────────────────────────────────

async def _cb_harvest(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant or plant.stage != "harvest":
            await query.answer("Куст ещё не готов! 🌱")
            return
        strain_data = STRAINS.get(plant.strain_key, {})
        strain_name = strain_data.get("name", "???")

    caption = (
        f"🌍🏆 <b>Мировой Харвест {strain_name}?</b>\n\n"
        f"🏔️→🕌→🇺🇸→🌍\n"
        f"Дух готов благословить сбор!\n\n"
        f"{DISCLAIMER_HARVEST}"
    )
    await _edit_screen(query, None, caption, harvest_confirm_kb())


async def _cb_harvest_confirm(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await query.answer("Нет куста 🤷")
            return
        result = await do_harvest(session, plant, user)
        await session.commit()

    if result["ok"]:
        photo = img.harvest_card(
            strain_name=STRAINS.get(plant.strain_key, {}).get("name", "???"),
            buds=result["buds"], coins=result["coins"],
        )
    else:
        photo = None
    await _edit_screen(query, photo, result["message"][:1024], after_harvest_kb())


# ─── Callback: SHARE ─────────────────────────────────────────────────

async def _cb_share(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await query.answer("Нет куста! 🌱")
            return
        strain_data = STRAINS.get(plant.strain_key, {})
        strain_name = strain_data.get("name", "???")
        stage_info = STAGE_INFO.get(plant.stage, STAGE_INFO["seed"])
        oe = _origin_emoji(strain_data)

    share_text = (
        f"🌿 Я выращиваю {strain_name} в @daily420_bot!\n"
        f"{oe} Стадия: {stage_info['emoji']} {stage_info['title']}\n"
        f"Путь: 🏔️→🕌→🇺🇸→🌍 | Попробуй! 🔥"
    )
    caption = f"📤 <b>Похвастайся кустом!</b>\n\n{share_text}"
    await _edit_screen(query, None, caption, share_inline_kb(share_text))


# ─── Callback: CUSTOMIZE ─────────────────────────────────────────────

async def _cb_customize(query, ctx) -> None:
    caption = "🎨 <b>Кастомизация</b>\n\n✏️ Переименуй куст\n🪴 Смени цвет горшка"
    await _edit_screen(query, None, caption, customize_kb())


async def _cb_pot(query, ctx, color: str) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id)
        plant = await get_active_plant(session, user.id)
        if plant:
            plant.pot_color = color
            await session.commit()
    await query.answer(f"Горшок: {color}")
    caption = f"🎨 <b>Кастомизация</b>\n\n✅ Горшок изменён на {color}!"
    await _edit_screen(query, None, caption, customize_kb())


async def _cb_rename_inline(query, ctx) -> None:
    await query.answer()
    # Не можем принять текст внутри inline-меню, просим в чат
    await _edit_screen(
        query, None,
        "✏️ Отправь новое имя для куста (до 30 символов) текстом в чат.\n"
        "Потом нажми /menu чтобы вернуться.",
        back_kb(),
    )
    ctx.user_data["awaiting_rename"] = True


# ─── Callback: CURE ──────────────────────────────────────────────────

async def _cb_cure_inline(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id)
        plant = await get_active_plant(session, user.id)
        if not plant:
            await query.answer("Нет куста")
            return
        msg = await cure_plant(session, plant)
        await session.commit()
    await query.answer(msg)
    # Возвращаемся в хаб
    await _cb_hub(query, ctx)


# ─── Callback: NEW GROW ──────────────────────────────────────────────

async def _cb_newgrow(query, ctx) -> None:
    tg = query.from_user
    async with async_session() as session:
        user = await get_or_create_user(session, tg.id, tg.username)
        plant = await get_active_plant(session, user.id)
        if plant:
            await query.answer("У тебя уже есть куст!")
            await _cb_hub(query, ctx)
            return
        plant, strain_data = await start_new_grow(session, user)
        await session.commit()

    oe = _origin_emoji(strain_data)
    caption = (
        f"🌰 <b>Твоё семечко!</b>\n\n"
        f"{oe} {strain_data['name']}\n"
        f"<i>{strain_data['desc']}</i>\n\n"
        f"🏔️ Впереди — Гималаи, Шёлковый путь и мировой харвест!\n"
        f"⚡ {config.ENERGY_MAX} действия в день. Удачи! 🔥"
    )
    photo = img.hub_card(
        strain_name=strain_data.get("name", "???"),
        stage_title="Семечко", origin=strain_data.get("origin", ""),
        energy=config.ENERGY_MAX, max_energy=config.ENERGY_MAX,
        coins=user.coins, progress=0.0, stage="seed",
    )
    kb = hub_kb(config.ENERGY_MAX, config.ENERGY_MAX, user.coins, "seed", False)
    await _edit_screen(query, photo, caption, kb)


# ─── Центральный роутер m: callbacks ─────────────────────────────────

async def menu_callback_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Единый обработчик всех m: коллбэков."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "m:hub":
        await _cb_hub(query, ctx)
    elif data in _MENU_ACTION_MAP:
        await _cb_action(query, ctx, _MENU_ACTION_MAP[data])
    elif data == "m:st":
        await _cb_status(query, ctx)
    elif data == "m:fact":
        await _cb_fact(query, ctx)
    elif data == "m:shop":
        await _cb_shop(query, ctx)
    elif data.startswith("m:buy:"):
        await _cb_buy(query, ctx, data[6:])
    elif data == "m:top":
        await _cb_top(query, ctx)
    elif data == "m:lore":
        await _cb_lore(query, ctx)
    elif data.startswith("m:lr:"):
        ch = int(data[5:]) if data[5:].isdigit() else 1
        await _cb_lore_chapter(query, ctx, max(1, min(ch, 4)))
    elif data == "m:game":
        await _cb_game(query, ctx)
    elif data.startswith("m:mg:"):
        await _cb_game_answer(query, ctx, data[5:])
    elif data == "m:harv":
        await _cb_harvest(query, ctx)
    elif data == "m:hc":
        await _cb_harvest_confirm(query, ctx)
    elif data == "m:share":
        await _cb_share(query, ctx)
    elif data == "m:cust":
        await _cb_customize(query, ctx)
    elif data.startswith("m:pot:"):
        await _cb_pot(query, ctx, data[6:])
    elif data == "m:ren":
        await _cb_rename_inline(query, ctx)
    elif data == "m:cure":
        await _cb_cure_inline(query, ctx)
    elif data == "m:newgrow":
        await _cb_newgrow(query, ctx)


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

    # Callback‑query (inline‑кнопки — старые)
    app.add_handler(CallbackQueryHandler(callback_buy, pattern=r"^buy:"))
    app.add_handler(CallbackQueryHandler(callback_close_shop, pattern=r"^close_shop$"))
    app.add_handler(CallbackQueryHandler(callback_cure, pattern=r"^cure$"))
    app.add_handler(CallbackQueryHandler(callback_harvest_confirm, pattern=r"^harvest_confirm$"))
    app.add_handler(CallbackQueryHandler(callback_harvest_wait, pattern=r"^harvest_wait$"))
    app.add_handler(CallbackQueryHandler(callback_pot_color, pattern=r"^pot:"))
    app.add_handler(CallbackQueryHandler(callback_rename, pattern=r"^rename$"))
    app.add_handler(CallbackQueryHandler(callback_minigame, pattern=r"^minigame:"))

    # Callback‑query — INLINE MENU SYSTEM (m: prefix)
    app.add_handler(CallbackQueryHandler(menu_callback_router, pattern=r"^m:"))

    # Текст (переименование) — последний, как fallback
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_rename_text
    ))
