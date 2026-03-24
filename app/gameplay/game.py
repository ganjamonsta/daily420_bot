"""Игровая логика — «Вырасти Куст» @daily420_bot.

Лор-интеграция: каждая стадия привязана к культуре,
при действиях выпадают исторические факты.
"""
from __future__ import annotations

import datetime as _dt
import random
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import config
from app.db.models import HarvestLog, Inventory, Plant, User
from app.gameplay.strains import STAGE_INFO, STRAINS, random_mutation, random_phrase, random_strain
from app.gameplay.lore import (
    STAGE_TRANSITION_LORE,
    cultural_phrase,
    random_fact_for_stage,
    random_lore_bonus,
    random_lore_fertilizer,
    random_lore_problem,
)


# ─── Helpers ──────────────────────────────────────────────────────────

def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _stage_for_points(pts: float) -> str:
    for stage, (lo, hi) in config.STAGES.items():
        if hi is None:
            if pts >= lo:
                return stage
        elif lo <= pts <= hi:
            return stage
    return "seed"


def _growth_multiplier_from_inventory(inventory: list[Inventory]) -> float:
    mul = 1.0
    for inv in inventory:
        if inv.equipped:
            item = config.SHOP_ITEMS.get(inv.item_key)
            if item:
                mul *= item["growth_bonus"]
    return mul


# ─── Get or create user ──────────────────────────────────────────────

async def get_or_create_user(
    session: AsyncSession, tg_id: int, username: Optional[str] = None
) -> User:
    user = await session.get(User, tg_id)
    if user is None:
        user = User(id=tg_id, username=username)
        session.add(user)
        await session.flush()
    elif username and user.username != username:
        user.username = username
        await session.flush()
    return user


# ─── Active plant ─────────────────────────────────────────────────────

async def get_active_plant(session: AsyncSession, user_id: int) -> Optional[Plant]:
    stmt = select(Plant).where(Plant.user_id == user_id, Plant.is_active == True)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ─── Start new grow ──────────────────────────────────────────────────

async def start_new_grow(session: AsyncSession, user: User) -> tuple[Plant, dict]:
    strain_key, strain_data = random_strain()
    plant = Plant(
        user_id=user.id,
        strain_key=strain_key,
        stage="seed",
        energy=config.ENERGY_MAX,
    )
    session.add(plant)
    await session.flush()
    return plant, strain_data


# ─── Energy ───────────────────────────────────────────────────────────

def _maybe_reset_energy(plant: Plant) -> None:
    now = _now()
    last = plant.last_energy_reset
    if last is None or (now - last.replace(tzinfo=_dt.timezone.utc)).total_seconds() >= config.ENERGY_COOLDOWN_HOURS * 3600:
        plant.energy = config.ENERGY_MAX
        plant.last_energy_reset = now


# ─── Perform action ──────────────────────────────────────────────────

ACTIONS = {
    "water":     {"emoji": "💧", "label": "Полить", "mood": "thirsty"},
    "light":     {"emoji": "💡", "label": "Дать свет", "mood": "dark"},
    "feed":      {"emoji": "🌿", "label": "Накормить", "mood": "hungry"},
    "ventilate": {"emoji": "🌬️", "label": "Проветрить / pH", "mood": "happy"},
}


async def perform_action(
    session: AsyncSession, plant: Plant, action_key: str, user: User
) -> dict:
    result: dict = {
        "ok": False,
        "message": "",
        "event": None,
        "stage_changed": False,
        "new_stage": None,
        "harvested": False,
    }

    if not plant.is_active:
        result["message"] = "У тебя нет активного куста! Жми /start 🌱"
        return result

    if plant.stage == "harvest":
        result["message"] = "Куст готов к харвесту! Жми «Собрать урожай» 🏆"
        return result

    _maybe_reset_energy(plant)

    if plant.energy <= 0:
        next_reset = plant.last_energy_reset.replace(tzinfo=_dt.timezone.utc) + _dt.timedelta(hours=config.ENERGY_COOLDOWN_HOURS)
        diff = next_reset - _now()
        hours = max(int(diff.total_seconds() // 3600), 0)
        mins = max(int((diff.total_seconds() % 3600) // 60), 0)
        result["message"] = (
            f"⚡ Энергия кончилась! Отдохни, братан.\n"
            f"Восстановится через {hours}ч {mins}мин."
        )
        return result

    if plant.is_sick:
        result["message"] = (
            f"🤒 Куст болеет ({plant.sickness})!\n"
            f"Сначала нажми «Вылечить», потом действуй."
        )
        result["sick"] = True
        return result

    action = ACTIONS.get(action_key)
    if not action:
        result["message"] = "Неизвестное действие 🤷"
        return result

    # Рассчитываем прирост
    base = config.BASE_GROWTH_PER_ACTION
    inv_mul = _growth_multiplier_from_inventory(user.inventory)
    growth = base * inv_mul

    # Рандомные события (с лором)
    event_msg = ""
    roll = random.random()
    if roll < config.EVENT_CHANCE_MUTATION:
        mut_key, mut_data = random_mutation()
        plant.mutated = True
        plant.mutation_strain = mut_key
        growth *= mut_data["yield_multiplier"]
        event_msg = f"\n\n🧬 МУТАЦИЯ! {mut_data['name']}\n{mut_data['desc']}"
        result["event"] = {"type": "mutation", "data": mut_data}
    elif roll < config.EVENT_CHANCE_MUTATION + config.EVENT_CHANCE_PROBLEM:
        problem = random_lore_problem()
        plant.is_sick = True
        plant.sickness = problem["sickness"]
        growth *= 0.5
        event_msg = f"\n\n⚠️ {problem['title']}\n{problem['text']}\n{problem['cure_text']}"
        result["event"] = {"type": "problem", "data": problem}
    elif roll < config.EVENT_CHANCE_MUTATION + config.EVENT_CHANCE_PROBLEM + config.EVENT_CHANCE_BONUS:
        bonus = random_lore_bonus()
        growth *= bonus["growth_multiplier"]
        event_msg = f"\n\n🎁 {bonus['title']}\n{bonus['text']}"
        result["event"] = {"type": "bonus", "data": bonus}

    plant.growth_points += growth
    plant.energy -= 1
    plant.last_action_at = _now()

    # Смена стадии
    old_stage = plant.stage
    new_stage = _stage_for_points(plant.growth_points)
    if new_stage != old_stage:
        plant.stage = new_stage
        result["stage_changed"] = True
        result["new_stage"] = new_stage

    if new_stage == "harvest":
        result["harvested"] = True

    # Текст удобрения
    fert = ""
    if action_key == "feed":
        fert = f"\nУдобрение: {random_lore_fertilizer()}"

    # Культурная фраза вместо обычной
    phrase = cultural_phrase(plant.stage)
    stage_info = STAGE_INFO[plant.stage]

    # Рандомный исторический факт (25% шанс)
    fact_msg = ""
    if random.random() < config.FACT_CHANCE:
        fact_msg = f"\n\n📜 {random_fact_for_stage(plant.stage)}"

    result["ok"] = True
    result["message"] = (
        f"{action['emoji']} {action['label']}!\n"
        f"+{growth:.0f} очков роста{fert}\n"
        f"⚡ Энергия: {plant.energy}/{config.ENERGY_MAX}\n\n"
        f"{stage_info['emoji']} {stage_info.get('culture_emoji', '')} "
        f"Стадия: {stage_info['title']}\n"
        f"📊 Рост: {plant.growth_points:.0f} очков\n\n"
        f"🌿 «{phrase}»"
        f"{event_msg}"
        f"{fact_msg}"
    )

    # Лор-нарратив при смене стадии
    if result["stage_changed"] and not result["harvested"]:
        lore_text = STAGE_TRANSITION_LORE.get(new_stage, "")
        if lore_text:
            result["message"] += f"\n\n{'─' * 28}\n{lore_text}"
        else:
            result["message"] += (
                f"\n\n🎉 НОВАЯ СТАДИЯ: {stage_info['emoji']} {stage_info['title']}!\n"
                f"{stage_info['text']}"
            )

    if result["harvested"]:
        lore_text = STAGE_TRANSITION_LORE.get("harvest", "")
        result["message"] += f"\n\n{'─' * 28}\n{lore_text}"
        result["message"] += "\n\nЖми «Собрать урожай»! 🏆"

    return result


# ─── Cure sickness ────────────────────────────────────────────────────

async def cure_plant(session: AsyncSession, plant: Plant) -> str:
    if not plant.is_sick:
        return "Куст здоров! Всё ок 💚"
    sickness = plant.sickness
    plant.is_sick = False
    plant.sickness = None
    return f"✅ Вылечено! ({sickness}) Куст снова здоров! 🌿"


# ─── Harvest ──────────────────────────────────────────────────────────

async def do_harvest(session: AsyncSession, plant: Plant, user: User) -> dict:
    if plant.stage != "harvest":
        return {"ok": False, "message": "Куст ещё не готов! Продолжай ухаживать 🌱"}

    strain_data = STRAINS.get(plant.strain_key, list(STRAINS.values())[0])
    base_min, base_max = strain_data["base_yield"]
    buds = random.randint(base_min, base_max)

    if plant.mutated and plant.mutation_strain:
        from app.gameplay.strains import MUTATIONS
        mut = MUTATIONS.get(plant.mutation_strain)
        if mut:
            buds = int(buds * mut["yield_multiplier"])

    inv_mul = _growth_multiplier_from_inventory(user.inventory)
    buds = int(buds * inv_mul)

    coins_earned = buds * config.BUDS_SELL_PRICE

    plant.is_active = False
    plant.harvested_at = _now()
    plant.buds_yield = buds

    user.total_harvests += 1
    user.total_buds += buds
    user.coins += coins_earned

    log = HarvestLog(user_id=user.id, strain_key=plant.strain_key, buds=buds)
    session.add(log)
    await session.flush()

    strain_name = strain_data["name"]
    origin_emoji = {"himalaya": "🏔️", "silk_road": "🕌", "america": "🇺🇸"}.get(
        strain_data.get("origin", ""), "🌍"
    )

    return {
        "ok": True,
        "message": (
            f"🌍🏆 *МИРОВОЙ ХАРВЕСТ ЗАВЕРШЁН!*\n\n"
            f"{origin_emoji} Стрейн: {strain_name}\n"
            f"🌸 Шишки: {buds} шт.\n"
            f"💰 Заработано: {coins_earned} монет\n\n"
            f"📊 Всего харвестов: {user.total_harvests}\n"
            f"📊 Всего шишек: {user.total_buds}\n"
            f"💰 Баланс: {user.coins} монет\n\n"
            f"🏔️→🕌→🇺🇸→🌍 Путь пройден!\n"
            f"Дух Древнего Гроубокса гордится тобой.\n\n"
            f"⚠️ Помни: это шутка. В реальной жизни — не повторяй!\n"
            f"Закон суров.\n\n"
            f"Жми /start чтобы начать новый гров! 🌱"
        ),
        "buds": buds,
        "coins": coins_earned,
    }


# ─── Status ───────────────────────────────────────────────────────────

def get_plant_status(plant: Plant, user: User) -> str:
    strain_data = STRAINS.get(plant.strain_key, {})
    strain_name = strain_data.get("name", plant.strain_key)
    origin_emoji = {"himalaya": "🏔️", "silk_road": "🕌", "america": "🇺🇸"}.get(
        strain_data.get("origin", ""), "🌍"
    )
    stage_info = STAGE_INFO.get(plant.stage, STAGE_INFO["seed"])

    _maybe_reset_energy(plant)

    days = (_now() - plant.started_at.replace(tzinfo=_dt.timezone.utc)).days

    if plant.is_sick:
        mood = "sick"
    elif plant.energy == 0:
        mood = "sad"
    elif plant.stage == "harvest":
        mood = "harvest_ready"
    else:
        mood = "happy"

    phrase = cultural_phrase(plant.stage)
    name_display = plant.custom_name or strain_name

    mutation_line = ""
    if plant.mutated and plant.mutation_strain:
        from app.gameplay.strains import MUTATIONS
        mut = MUTATIONS.get(plant.mutation_strain, {})
        mutation_line = f"\n🧬 Мутация: {mut.get('name', '???')}"

    sick_line = ""
    if plant.is_sick:
        sick_line = f"\n🤒 Болезнь: {plant.sickness} — нажми «Вылечить»!"

    return (
        f"🌿 {name_display} {origin_emoji}\n"
        f"{'─' * 24}\n"
        f"{stage_info['emoji']} {stage_info.get('culture_emoji', '')} "
        f"Стадия: {stage_info['title']}\n"
        f"📊 Рост: {plant.growth_points:.0f} очков\n"
        f"📅 День: {days}\n"
        f"⚡ Энергия: {plant.energy}/{config.ENERGY_MAX}\n"
        f"{plant.pot_color} Горшок"
        f"{mutation_line}"
        f"{sick_line}\n\n"
        f"🌿 «{phrase}»\n"
        f"{'─' * 24}\n"
        f"💰 Монеты: {user.coins} | 🏆 Харвестов: {user.total_harvests}"
    )


# ─── Miss day penalty ─────────────────────────────────────────────────

def check_miss_penalty(plant: Plant) -> Optional[str]:
    if not plant.last_action_at:
        return None
    diff = _now() - plant.last_action_at.replace(tzinfo=_dt.timezone.utc)
    missed_days = int(diff.total_seconds() // 86400)
    if missed_days >= 2:
        phrase = random_phrase("sad")
        return (
            f"😢 Ты не заходил {missed_days} дней!\n"
            f"Куст грустит и рост замедлился.\n\n"
            f"🌿 «{phrase}»"
        )
    return None
