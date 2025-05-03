# handlers/filter.py

import re
import time
import sys
sys.path.append("./censure")  # allow module import from git submodule

from libs.censure import Censor

censor_ru = Censor.get(lang='ru')
censor_en = Censor.get(lang='en')

from collections import defaultdict
from datetime import timedelta, datetime

from aiogram import Router, F
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ChatType, ChatMemberStatus

from loader import bot
from db import (
    get_link_filter, set_link_filter,
    get_caps_filter, set_caps_filter,
    get_spam_filter, set_spam_filter,
    get_swear_filter, set_swear_filter,
    get_keywords_filter, set_keywords_filter,
    get_keywords,
    get_warn_count, add_warn, reset_warns,
    get_mute_info, add_mute, reset_mutes,
)
from config import ADMIN_IDS

router = Router()

# параметры антифлуда
user_messages = defaultdict(list)
SPAM_LIMIT    = 5
SPAM_INTERVAL = 10
BASE_MUTE_SEC = 30

# параметры антиспама стикерами
user_sticker_counts = defaultdict(int)
STICKER_LIMIT = 2


def is_admin(user_id: int) -> bool:
    # Суперпользователи бота
    return user_id in ADMIN_IDS

async def is_chat_admin(chat_id: int, user_id: int) -> bool:
    # Админы и создатель группы освобождаются от фильтров
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except:
        return False

url_pattern   = re.compile(r"https?://\S+|www\.\S+|t\.me/\S+")
emoji_pattern = re.compile(
    "[\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\u2600-\u26FF\u2700-\u27BF]+",
    flags=re.UNICODE
)

async def punish_for_spam(user_id: int, chat_id: int, message: Message):
    # добавляем запись о муте
    add_mute(user_id, chat_id, message.from_user.username or message.from_user.full_name)
    count, _ = get_mute_info(user_id, chat_id)
    duration = BASE_MUTE_SEC * (2 ** (count - 1))
    until = message.date + timedelta(seconds=duration)

    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until
    )

    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>"
    await message.answer(
        f"⏳ {mention} замучен за флуд на {duration} сек.",
        parse_mode="HTML"
    )

async def issue_warn_or_mute(user_id: int, chat_id: int, message: Message, reason: str):
    # удаляем нарушившее сообщение и выдаём варн/мут
    await message.delete()
    username = message.from_user.username or message.from_user.full_name
    add_warn(user_id, chat_id, username)
    warns = get_warn_count(user_id, chat_id)

    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>"

    if warns >= 3:
        await punish_for_spam(user_id, chat_id, message)
        reset_warns(user_id, chat_id)
    else:
        await message.answer(
            f"⚠️ {mention} получил варн ({warns}/3) за {reason}.",
            parse_mode="HTML"
        )

@router.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))
async def moderation_filters(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text    = message.text or ""

    # освобождаем от всех фильтров админов чата
    if await is_chat_admin(chat_id, user_id):
        return

    # 0) пропускаем, если всё ещё в муте
    count, last = get_mute_info(user_id, chat_id)
    if last:
        duration = BASE_MUTE_SEC * (2 ** (count - 1))
        if datetime.utcnow() < last + timedelta(seconds=duration):
            return

    # 1) антифлуд: >SPAM_LIMIT сообщений за SPAM_INTERVAL сек.
    now = time.time()
    recent = [t for t in user_messages[user_id] if now - t < SPAM_INTERVAL]
    recent.append(now)
    user_messages[user_id] = recent
    if len(recent) > SPAM_LIMIT:
        return await punish_for_spam(user_id, chat_id, message)

    # 1.1) антиспам стикерами: >STICKER_LIMIT подряд → варн/мут
    if message.sticker:
        user_sticker_counts[user_id] += 1
        if user_sticker_counts[user_id] > STICKER_LIMIT:
            return await issue_warn_or_mute(user_id, chat_id, message, "стикеры")
        return
    else:
        user_sticker_counts[user_id] = 0

    # 2) фильтр ссылок → варн
    if get_link_filter(chat_id) and url_pattern.search(text):
        return await issue_warn_or_mute(user_id, chat_id, message, "ссылки")

    # 3) анти-капс
    if get_caps_filter(chat_id):
        if not url_pattern.search(text) and not emoji_pattern.fullmatch(text.strip()):
            letters = re.findall(r"[A-Za-zА-Яа-яЁё]", text)
            if letters and len(letters) > 6:
                ratio = sum(1 for c in letters if c.isupper()) / len(letters)
                if ratio > 0.7:
                    return await message.delete()

    # 4) антиспам-символы (5+ подряд) → варн
    if get_spam_filter(chat_id) and re.search(r"(.)\1{5,}", text):
        return await issue_warn_or_mute(user_id, chat_id, message, "спам символов")

    # 5) антимат
    if get_swear_filter(chat_id):
        line_info_ru = censor_ru.clean_line(text)
        line_info_en = censor_en.clean_line(text)
        if line_info_ru[1] or line_info_ru[2] or line_info_en[1] or line_info_en[2]:
            return await issue_warn_or_mute(user_id, chat_id, message, "мат")

    # 6) ключевые слова → варн
    if get_keywords_filter(chat_id):
        for kw in get_keywords(chat_id):
            if kw.lower() in text.lower():
                return await issue_warn_or_mute(user_id, chat_id, message, f"ключевое слово «{kw}»")


def register_handlers_filter(dp):
    dp.include_router(router)
