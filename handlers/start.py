# start.py

from aiogram import Router, types, F
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

router = Router()

# — текст главного меню
MENU_TEXT = (
    '😈 <b>Devil | </b>'
    '<a href="https://t.me/managrbot">Чат-менеджер</a> приветствует Вас!\n'
    'Я могу предложить следующие темы:\n\n'
    '1). <b>установка</b> — инструкция установки Devil;\n'
    '2). <b>команды</b> — список команд бота;\n\n'
    '🔈 Для вызова клавиатуры с основными темами, введите <b>начать</b> или <b>помощь</b>.'
)

# — inline‑клавиатура
inline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="Добавить в свой чат",
            url=(
                "https://t.me/managrbot?startgroup=devil&admin="
                "change_info+restrict_members+delete_messages+pin_messages+invite_users"
            )
        )
    ]
])

# — reply‑клавиатура
reply_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="Мои чаты")],
        [KeyboardButton(text="Установка"), KeyboardButton(text="Команды")]
    ]
)


@router.message(
    CommandStart(),
    F.chat.type == ChatType.PRIVATE
)
async def cmd_start(message: types.Message):
    # 1) Отправляем сообщение с inline‑клавиатурой
    await message.answer(MENU_TEXT, reply_markup=inline_kb, parse_mode="HTML")
    # 2) Затем — с reply‑клавиатурой
    await message.answer("Выберите действие:", reply_markup=reply_kb)


def register_handlers_start(dp):
    dp.include_router(router)
