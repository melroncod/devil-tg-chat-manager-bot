# config.py
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

# Преобразуем строку ID в список чисел
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))

# Настройки для фильтрации
ENABLE_LINK_FILTER_DEFAULT = True  # По умолчанию фильтрация включена
