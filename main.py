# main.py

import asyncio
import logging

from config import ADMIN_IDS
from db import add_admin, create_tables

from loader import bot, dp

from handlers.start import register_handlers_start
from handlers.aliases import register_handlers_aliases
from handlers.filter import register_handlers_filter
from handlers.help import register_handlers_help
from handlers.setup import register_handlers_setup
from handlers.user_chats import register_handlers_user_chats

async def main():
    # (либо перенести сюда, либо оставить в loader.py)
    logging.info("Запускаем бот-менеджер...")

    # Инициализация БД
    create_tables()
    for admin in ADMIN_IDS:
        add_admin(admin)

    # Регистрация всех хендлеров в едином dp
    register_handlers_start(dp)
    register_handlers_aliases(dp)
    register_handlers_filter(dp)
    register_handlers_help(dp)
    register_handlers_setup(dp)
    register_handlers_user_chats(dp)

    # Запуск поллинга на том же bot и dp
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
