from dotenv import load_dotenv
import os

load_dotenv()

# Telegram API токен
API_TOKEN = os.getenv('API_TOKEN')

# Преобразуем строку ID в список чисел
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))

# Настройки для фильтрации
ENABLE_LINK_FILTER_DEFAULT = True  # По умолчанию фильтрация включена

# Настройки подключения к базе данных
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = int(os.getenv('POSTGRES_PORT', 5432))
DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
