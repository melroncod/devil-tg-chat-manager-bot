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
    # 1) Настройка логирования
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("Запускаем бот-менеджер...")

    # 2) Инициализация/миграция схемы в PostgreSQL
    create_tables()
    for admin_id in ADMIN_IDS:
        add_admin(admin_id)

    # 3) Регистрируем все хендлеры
    register_handlers_start(dp)
    register_handlers_aliases(dp)
    register_handlers_filter(dp)
    register_handlers_user_chats(dp)
    register_handlers_help(dp)
    register_handlers_setup(dp)

    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
