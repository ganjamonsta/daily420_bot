"""Main entrypoint package for «Вырасти Куст» @daily420_bot."""
from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder

from app.core import config
from app.db.models import init_db
from app.ui.handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(app) -> None:
    await init_db()
    logger.info("Database initialized")


def main() -> None:
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан! Создай .env файл (см. .env.example)")

    app = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    register_handlers(app)
    logger.info("«Вырасти Куст» @daily420_bot starting…")
    app.run_polling(drop_pending_updates=True)
