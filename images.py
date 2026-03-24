"""Генерация карточек-баннеров для inline-меню — «Вырасти Куст» @daily420_bot.

Если Pillow установлен — генерирует PNG-карточки с цветовой схемой
по культуре. Если нет — все функции возвращают None, бот работает в
текстовом режиме (graceful degradation).
"""
from __future__ import annotations

import io
from typing import Sequence

try:
    from PIL import Image, ImageDraw, ImageFont

    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

# ═══ Палитры ══════════════════════════════════════════════════════════

PALETTES = {
    "himalaya":  {"bg1": (15, 40, 75),  "bg2": (30, 70, 120), "accent": (70, 140, 190), "bar": (52, 152, 219)},
    "silk_road": {"bg1": (75, 40, 15),  "bg2": (115, 70, 30), "accent": (180, 120, 40), "bar": (218, 165, 32)},
    "america":   {"bg1": (100, 25, 20), "bg2": (155, 55, 40), "accent": (220, 100, 50), "bar": (230, 126, 34)},
    "world":     {"bg1": (15, 60, 35),  "bg2": (30, 100, 55), "accent": (39, 174, 96),  "bar": (46, 204, 113)},
    "shop":      {"bg1": (60, 35, 10),  "bg2": (100, 65, 25), "accent": (200, 150, 50), "bar": (218, 165, 32)},
    "lore":      {"bg1": (45, 30, 20),  "bg2": (80, 55, 35),  "accent": (160, 120, 60), "bar": (200, 160, 80)},
    "game":      {"bg1": (35, 15, 60),  "bg2": (65, 35, 105), "accent": (140, 80, 200), "bar": (170, 100, 230)},
    "top":       {"bg1": (15, 35, 60),  "bg2": (30, 60, 100), "accent": (60, 130, 200), "bar": (255, 215, 0)},
    "fact":      {"bg1": (50, 40, 25),  "bg2": (85, 70, 45),  "accent": (180, 140, 70), "bar": (210, 170, 80)},
}

STAGE_TO_PALETTE = {
    "seed": "himalaya", "sprout": "himalaya",
    "vegetative": "silk_road", "flowering": "america",
    "harvest": "world",
}

CARD_W = 620

# ═══ Шрифты ═══════════════════════════════════════════════════════════

_font_cache: dict = {}
_FONT_PATHS = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _font(size: int):
    if size in _font_cache:
        return _font_cache[size]
    if not PILLOW_OK:
        return None
    for p in _FONT_PATHS:
        try:
            f = ImageFont.truetype(p, size)
            _font_cache[size] = f
            return f
        except (OSError, IOError):
            continue
    try:
        f = ImageFont.load_default(size)
    except TypeError:
        f = ImageFont.load_default()
    _font_cache[size] = f
    return f


# ═══ Отрисовка ════════════════════════════════════════════════════════

def _gradient(draw, w: int, h: int, c1: tuple, c2: tuple):
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def make_card(
    title: str,
    body_lines: Sequence[str],
    palette: str = "world",
    progress: float | None = None,
    footer: str = "",
) -> io.BytesIO | None:
    """Универсальный генератор карточек. Возвращает BytesIO PNG или None."""
    if not PILLOW_OK:
        return None

    pal = PALETTES.get(palette, PALETTES["world"])

    # Высота = заголовок + строки + прогресс-бар + подвал + отступы
    n = len(body_lines)
    h = 90 + n * 30 + 10
    if progress is not None:
        h += 44
    if footer:
        h += 28
    h += 24
    h = max(h, 180)

    img = Image.new("RGB", (CARD_W, h))
    draw = ImageDraw.Draw(img)
    _gradient(draw, CARD_W, h, pal["bg1"], pal["bg2"])

    # Акцентная полоса под заголовком
    draw.rectangle([(0, 72), (CARD_W, 76)], fill=pal["accent"])

    # Заголовок
    ft = _font(26)
    draw.text((28, 22), title, fill="white", font=ft)

    # Тело
    fb = _font(18)
    y = 92
    for line in body_lines:
        draw.text((28, y), line, fill=(215, 215, 215), font=fb)
        y += 30

    # Прогресс-бар
    if progress is not None:
        y += 6
        bar_x = 28
        bar_end = CARD_W - 90
        bar_w = bar_end - bar_x
        bar_h = 22
        draw.rounded_rectangle(
            [(bar_x, y), (bar_end, y + bar_h)], radius=11, fill=(35, 35, 35),
        )
        fill_w = max(int(bar_w * min(progress, 1.0)), 2)
        if fill_w > 4:
            draw.rounded_rectangle(
                [(bar_x, y), (bar_x + fill_w, y + bar_h)], radius=11, fill=pal["bar"],
            )
        pct_text = f"{int(progress * 100)}%"
        draw.text((bar_end + 10, y + 1), pct_text, fill="white", font=_font(16))
        y += bar_h + 8

    # Подвал
    if footer:
        draw.text((28, h - 34), footer, fill=(120, 120, 120), font=_font(13))

    # Рамка
    draw.rectangle([(0, 0), (CARD_W - 1, h - 1)], outline=pal["accent"], width=2)

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


# ═══ Карточки для конкретных экранов ══════════════════════════════════

ORIGIN_LABEL = {
    "himalaya": "Гималаи", "silk_road": "Шёлковый путь",
    "america": "Америка 420", "": "Мир",
}


def hub_card(
    strain_name: str, stage_title: str, origin: str,
    energy: int, max_energy: int, coins: int,
    progress: float, stage: str,
) -> io.BytesIO | None:
    pal = STAGE_TO_PALETTE.get(stage, "world")
    origin_label = ORIGIN_LABEL.get(origin, "Мир")
    return make_card(
        title="ВЫРАСТИ КУСТ",
        body_lines=[
            f"Стрейн: {strain_name}",
            f"Стадия: {stage_title}  ({origin_label})",
            f"Энергия: {energy}/{max_energy}   Монеты: {coins}",
        ],
        palette=pal,
        progress=progress,
        footer="@daily420_bot  —  виртуальная шутка, не повторяй!",
    )


def status_card(
    strain_name: str, stage_title: str, origin: str,
    energy: int, max_energy: int, coins: int,
    growth: float, day: int, health: str,
    progress: float, stage: str,
) -> io.BytesIO | None:
    pal = STAGE_TO_PALETTE.get(stage, "world")
    lines = [
        f"Стрейн: {strain_name}",
        f"Стадия: {stage_title}",
        f"Рост: {growth:.0f} очков  |  День: {day}",
        f"Энергия: {energy}/{max_energy}  |  Монеты: {coins}",
        f"Здоровье: {health}",
    ]
    return make_card(
        title="СТАТУС КУСТА",
        body_lines=lines,
        palette=pal,
        progress=progress,
        footer="@daily420_bot",
    )


def shop_card(coins: int) -> io.BytesIO | None:
    return make_card(
        title="БАЗАР ШЁЛКОВОГО ПУТИ",
        body_lines=[
            f"Монеты: {coins}",
            "",
            "Выбери товар в кнопках ниже",
        ],
        palette="shop",
        footer="Дух одобряет покупки!",
    )


def lore_card() -> io.BytesIO | None:
    return make_card(
        title="ДУХ ДРЕВНЕГО ГРОУБОКСА",
        body_lines=[
            "Я прошёл путь от Гималаев",
            "через Шёлковый путь",
            "до 420-Калифорнии.",
            "",
            "Выбери главу моей истории:",
        ],
        palette="lore",
        footer="Виртуальная шутка. Не повторяй!",
    )


def fact_card(culture: str = "world") -> io.BytesIO | None:
    pal = {"himalaya": "himalaya", "silk_road": "silk_road",
           "america": "america"}.get(culture, "fact")
    return make_card(
        title="ИСТОРИЧЕСКИЙ ФАКТ",
        body_lines=["Дух Древнего Гроубокса рассказывает..."],
        palette=pal,
        footer="Это образовательный контент, а не пропаганда.",
    )


def game_card() -> io.BytesIO | None:
    return make_card(
        title="МИНИ-ИГРА ДУХА",
        body_lines=[
            "Ответь на вопрос",
            "и получи бонусные монеты!",
        ],
        palette="game",
        footer="Удачи, гровер!",
    )


def top_card() -> io.BytesIO | None:
    return make_card(
        title="ТОП ГРОВЕРОВ",
        body_lines=["Лучшие за неделю:"],
        palette="top",
        footer="Расти дальше!",
    )


def action_card(
    action_emoji: str, action_label: str,
    growth: float, energy: int, max_energy: int,
    stage_title: str, stage: str,
) -> io.BytesIO | None:
    pal = STAGE_TO_PALETTE.get(stage, "world")
    return make_card(
        title=f"{action_label.upper()}!",
        body_lines=[
            f"+{growth:.0f} очков роста",
            f"Энергия: {energy}/{max_energy}",
            f"Стадия:  {stage_title}",
        ],
        palette=pal,
        footer="@daily420_bot",
    )


def harvest_card(
    strain_name: str, buds: int, coins: int,
) -> io.BytesIO | None:
    return make_card(
        title="МИРОВОЙ ХАРВЕСТ!",
        body_lines=[
            f"Стрейн: {strain_name}",
            f"Шишки: {buds} шт.",
            f"Заработано: {coins} монет",
            "",
            "Дух Древнего Гроубокса гордится!",
        ],
        palette="world",
        progress=1.0,
        footer="Путь пройден: Гималаи > Шёлковый путь > Америка > Мир",
    )


def no_plant_card() -> io.BytesIO | None:
    return make_card(
        title="ВЫРАСТИ КУСТ",
        body_lines=[
            "У тебя нет куста!",
            "Жми /start чтобы получить семечко",
            "от Духа Древнего Гроубокса.",
        ],
        palette="world",
        footer="@daily420_bot",
    )
