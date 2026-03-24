"""Точка входа — «Вырасти Куст» @daily420_bot."""
import asyncio
import logging

from telegram.ext import ApplicationBuilder

import config
from handlers import register_handlers
from models import init_db

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


if __name__ == "__main__":
    main()
