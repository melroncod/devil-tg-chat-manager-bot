# loader.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import API_TOKEN

# Настройка логирования (общая для всего бота)
logging.basicConfig(level=logging.INFO)
logging.info("Инициализация loader...")

# Глобальный экземпляр бота
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Глобальный диспетчер — регистрируем в нём все роутеры
dp = Dispatcher()
