import logging
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatType

router = Router()


@router.message(lambda msg: msg.chat.type == ChatType.PRIVATE
                            and msg.text
                            and msg.text.lower() == "установка")
async def cmd_installation(message: Message):
    logging.info("✔️ Попали в cmd_installation")
    text = (
        '⚙️ <b>Установка </b>'
        '<a href="https://t.me/managrbot"> Devil | Чат-менеджер</a> в Ваш чат:\n\n'
        '1) Пригласите бота <a href="https://t.me/managrbot?startgroup=devil&admin=change_info+restrict_members+delete_messages+pin_messages+invite_users">по данной ссылке</a>;\n'
        '2) Нажмите на название своего чата;\n'
        '3) Назначьте бота администратором;\n'
        '4) Установите должность.\n\n'
        '❗️ <b>Важно:</b> не отключайте уже установленные права!'
    )

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Пригласить бота",
            url="https://t.me/managrbot?startgroup=devil&admin=change_info+restrict_members+delete_messages+pin_messages+invite_users"
        )
    ]])
    await message.answer(text, parse_mode="HTML", reply_markup=inline_kb, disable_web_page_preview=True)


def register_handlers_setup(dp):
    dp.include_router(router)
