from aiogram import Router, types, F
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

router = Router()

@router.message(
    CommandStart(),
    F.chat.type == ChatType.PRIVATE
)
async def cmd_start(message: types.Message):
    text = (
        '😈 <b>Devil | </b>'
        '<a href="https://t.me/managrbot">Чат-менеджер</a> приветствует Вас!\n'
        'Я могу предложить следующие темы:\n\n'
        '1). <b>установка</b> — инструкция установки Devil;\n'
        '2). <b>команды</b> — список команд бота;\n\n'
        '🔈 Для вызова клавиатуры с основными темами, введите <b>начать</b> или <b>помощь</b>.'
    )

    # 1) Inline-клавиатура с кнопкой "Добавить в свой чат"
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Добавить в свой чат",
            url=(
                "https://t.me/managrbot?startgroup=devil&admin="
                "change_info+restrict_members+delete_messages+pin_messages+invite_users"
            )
        )]
    ])

    # 2) Reply-клавиатура с общими командами
    reply_kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Мои чаты")],
            [KeyboardButton(text="Установка"), KeyboardButton(text="Команды")]
        ]
    )

    # Отправляем сначала сообщение с inline
    await message.answer(text, reply_markup=inline_kb, parse_mode="HTML")
    # А потом — с reply
    await message.answer("Выберите действие:", reply_markup=reply_kb)


def register_handlers_start(dp):
    dp.include_router(router)
