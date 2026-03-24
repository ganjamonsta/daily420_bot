"""Конфигурация «Вырасти Куст» — @daily420_bot."""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ─────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_NAME = "Вырасти Куст 🌿"
BOT_USERNAME = "@daily420_bot"

# ─── Database ─────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///growbox.db")

# ─── Game balance ─────────────────────────────────────────────────────
ENERGY_MAX = 16                # макс действий в день
ENERGY_COOLDOWN_HOURS = 4    # восстановление энергии
BASE_GROWTH_PER_ACTION = 3   # базовые очки роста за действие
MISS_DAY_PENALTY = 0.5        # множитель замедления при пропуске дня
FACT_CHANCE = 0.25            # 25% шанс исторического факта при действии

# ─── Стадии роста (порог очков) ───────────────────────────────────────
STAGES = {
    "seed":       (0, 29),
    "sprout":     (30, 99),
    "vegetative": (100, 249),
    "flowering":  (250, 449),
    "harvest":    (450, None),
}

# Время роста (дни)
HARVEST_MIN_DAYS = 3
HARVEST_MAX_DAYS = 7

# ─── Random events (вероятности за одно действие) ─────────────────────
EVENT_CHANCE_BONUS = 0.10     # 10% бонус‑событие
EVENT_CHANCE_PROBLEM = 0.08   # 8% проблема
EVENT_CHANCE_MUTATION = 0.03  # 3% мутация

# ─── Shop prices (coins) ─────────────────────────────────────────────
SHOP_ITEMS = {
    "led_1000w":       {"name": "LED 1000W 💡", "price": 50, "growth_bonus": 1.15},
    "big_pot":         {"name": "Большой горшок 🪴", "price": 40, "growth_bonus": 1.10},
    "himalayan_soil":  {"name": "Гималайский грунт 🏔️", "price": 60, "growth_bonus": 1.12},
    "moroccan_mix":    {"name": "Марокканский микс 🕌", "price": 70, "growth_bonus": 1.18},
    "cali_nutrients":  {"name": "Калифорнийские нутры 🇺🇸", "price": 90, "growth_bonus": 1.22},
    "autoflower_gen":  {"name": "Автоцвет-генетика 🧬", "price": 100, "growth_bonus": 1.20},
    "silk_road_spice": {"name": "Специи Шёлкового пути 🐪", "price": 80, "growth_bonus": 1.15},
    "coco_substrate":  {"name": "Кокос из Ашана 🥥", "price": 30, "growth_bonus": 1.08},
}

# ─── Sell price per bud ──────────────────────────────────────────────
BUDS_SELL_PRICE = 2  # монеты за 1 шишку

# ─── Leaderboard ─────────────────────────────────────────────────────
LEADERBOARD_SIZE = 10
