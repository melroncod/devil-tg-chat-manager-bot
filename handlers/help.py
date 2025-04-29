# handlers/help.py
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

router = Router()

@router.message(Command("help"), F.chat.type == ChatType.PRIVATE)
async def help_command(message: Message):
    await send_help(message)

@router.message(F.text.lower() == "команды", F.chat.type == ChatType.PRIVATE)
async def help_text(message: Message):
    await send_help(message)

async def send_help(message: Message):
    logging.info(f"Получен /help от {message.from_user.id}")
    help_text = (
        "📋 <b>Справка по командам бота-менеджера:</b>\n"
        "Команды можно вводить с префиксом <code>/</code> или <code>!</code>.\n\n"
        "<u>🔹 Приватный режим</u>:\n"
        "/start — стартовое меню и выбор чатов для управления\n"
        "/help, команды — эта справка\n\n"
        "<u>⚙️ Управление чатом (только для админов)</u>:\n"
        "/rules — показать правила чата\n"
        "/setup — регистрация чата для управления\n"
        "/ban [@username|reply] — забанить пользователя\n"
        "/unban [@username|reply] — разбанить пользователя\n"
        "/mute [@username|reply] [часы] — замутить пользователя\n"
        "/unmute [@username|reply] — размутить пользователя\n"
        "/checkperms [@username|reply] — проверить права пользователя\n"
        "/ro — переключить режим только для чтения\n"
        "/resetwarn [@username|reply] — обнулить варны пользователя\n"
        "/resetwarnsall — обнулить все варны в чате\n\n"
        "<u>🔗 Фильтры в меню управления</u>:\n"
        "Переключайте фильтры ссылок, капса, спама, стикеров, мата и ключевых слов через графический интерфейс.\n"
        "Статус каждого фильтра отображается в меню."
    )
    await message.answer(help_text, parse_mode="HTML")


def register_handlers_help(dp):
    dp.include_router(router)
