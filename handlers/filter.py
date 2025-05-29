import re
import time
import sys

sys.path.append("./censure")  # submodule with libs.censure
from libs.censure import Censor

censor_ru = Censor.get(lang='ru')
censor_en = Censor.get(lang='en')

from collections import defaultdict
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from loader import bot
from db import (
    get_link_filter,
    get_caps_filter,
    get_spam_filter,
    get_swear_filter,
    get_keywords_filter,
    get_keywords,
    set_sticker_filter,
    get_warn_count,
    add_warn,
    reset_warns,
    get_mute_info,
    add_mute,
    reset_mutes,
    get_devil_mode,
    get_admins
)

router = Router()

# антифлуд
user_messages = defaultdict(list)
SPAM_LIMIT = 5
SPAM_INTERVAL = 10

# анти-стикеры
user_sticker_counts = defaultdict(int)
STICKER_LIMIT = 2

# градация длительностей мьютов
# 1) 1 мин, 2) 10 мин, 3) 1 ч, 4) 1 д, 5) 7 д, 6+) вечный
MUTE_DURATIONS = [
    60,             # 1 минута
    10 * 60,        # 10 минут
    60 * 60,        # 1 час
    24 * 60 * 60,   # 1 день
    7 * 24 * 60 * 60,# 7 дней
    None            # вечный
]

url_pattern = re.compile(r"https?://\S+|www\.\S+|t\.me/\S+")
emoji_pattern = re.compile(
    "[\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\u2600-\u26FF\u2700-\u27BF]+",
    flags=re.UNICODE
)

# Для Devil Mode: отслеживаем время последнего предупреждения для каждого пользователя
last_devil_warning: dict[int, float] = defaultdict(float)
# Карантин между предупреждениями (в секундах)
DEVIL_WARNING_COOLDOWN = 5.0


async def punish_for_spam(user_id: int, chat_id: int, message: Message):
    add_mute(user_id, chat_id, message.from_user.username or message.from_user.full_name)
    count, last_mute_dt = get_mute_info(user_id, chat_id)

    if count <= len(MUTE_DURATIONS):
        duration = MUTE_DURATIONS[count - 1]
    else:
        duration = None

    if duration is None:
        until_date = 0  # вечный мут
        human = "вечный"
    else:
        until_date = int(time.time() + duration)
        human = f"{duration} сек"

    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until_date
    )

    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>"
    try:
        await message.answer(
            f"⏳ {mention} замучен за флуд на {human}. (уровень {count})",
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass


async def issue_warn_or_mute(user_id: int, chat_id: int, message: Message, reason: str):
    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    username = message.from_user.username or message.from_user.full_name
    add_warn(user_id, chat_id, username)
    warns = get_warn_count(user_id, chat_id)

    mention = f"<a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>"
    if warns >= 3:
        await punish_for_spam(user_id, chat_id, message)
        reset_warns(user_id, chat_id)
    else:
        try:
            await message.answer(
                f"⚠️ {mention} получил варн ({warns}/3) за {reason}.",
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            pass


@router.message(
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]),
    F.new_chat_members.is_(None),
    F.left_chat_member.is_(None)
)
async def moderation_filters(message: Message):
    chat_id = message.chat.id

    # пропускаем сообщения от имени чата
    if message.sender_chat:
        return

    user = message.from_user
    if not user:
        return

    user_id = user.id
    # кастомные админы из БД (создатель бота и пр.) освобождены
    if user_id in get_admins():
        return

    # штатные админы группы тоже освобождены
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        if m.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
            return
    except:
        pass

    text = message.text or ""

    # Devil Mode: разрешены только сообщения с матом
    if get_devil_mode(chat_id):
        ru = censor_ru.clean_line(text)
        en = censor_en.clean_line(text)
        has_mat = (ru[1] or ru[2] or en[1] or en[2])

        if not has_mat:
            now_ts = time.time()
            last_ts = last_devil_warning.get(user_id, 0.0)

            # Если прошло меньше кулдауна между предупреждениями, просто удаляем без отправки
            if now_ts - last_ts < DEVIL_WARNING_COOLDOWN:
                try:
                    await message.delete()
                except TelegramBadRequest:
                    pass
                return

            # Иначе обновляем время последнего предупреждения
            last_devil_warning[user_id] = now_ts
            try:
                await message.delete()
            except TelegramBadRequest:
                pass

            mention = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
            try:
                await message.answer(
                    f"🚫 {mention}, в Devil mode вы можете отправлять <b>только</b> сообщения с ненормативной лексикой.\n"
                    "Чтобы ваше сообщение не удалялось — добавьте в него мат.",
                    parse_mode="HTML"
                )
            except TelegramBadRequest:
                pass

        return

    # Проверка мута
    count, last_mute_dt = get_mute_info(user_id, chat_id)
    if last_mute_dt:
        lvl = count if count > 0 else 1
        duration = MUTE_DURATIONS[lvl - 1] if lvl <= len(MUTE_DURATIONS) else None
        if duration is None:
            return
        if time.time() < last_mute_dt.timestamp() + duration:
            return

    # Антифлуд
    if get_spam_filter(chat_id):
        now = time.time()
        recent = [t for t in user_messages[user_id] if now - t < SPAM_INTERVAL]
        recent.append(now)
        user_messages[user_id] = recent
        if len(recent) > SPAM_LIMIT:
            return await punish_for_spam(user_id, chat_id, message)
    else:
        user_messages[user_id].clear()

    # Анти-стикеры
    if message.sticker:
        if set_sticker_filter(chat_id):
            user_sticker_counts[user_id] += 1
            if user_sticker_counts[user_id] > STICKER_LIMIT:
                return await issue_warn_or_mute(user_id, chat_id, message, "стикеры")
        else:
            user_sticker_counts[user_id] = 0
        return
    else:
        user_sticker_counts[user_id] = 0

    # Фильтр ссылок
    if get_link_filter(chat_id) and url_pattern.search(text):
        return await issue_warn_or_mute(user_id, chat_id, message, "ссылки")

    # Анти-капс
    if get_caps_filter(chat_id):
        letters = re.findall(r"[A-Za-zА-Яа-яЁё]", text)
        if letters and len(letters) > 6:
            ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if ratio > 0.7:
                return await issue_warn_or_mute(user_id, chat_id, message, "капс")

    # Спам-символы
    if get_spam_filter(chat_id) and re.search(r"(.)\1{5,}", text):
        return await issue_warn_or_mute(user_id, chat_id, message, "спам символов")

    # Антимат
    if get_swear_filter(chat_id):
        ru = censor_ru.clean_line(text)
        en = censor_en.clean_line(text)
        has_ru = (len(ru) > 2 and (ru[1] or ru[2]))
        has_en = (len(en) > 2 and (en[1] or en[2]))
        if has_ru or has_en:
            return await issue_warn_or_mute(user_id, chat_id, message, "мат")

    # Ключевые слова
    if get_keywords_filter(chat_id):
        for kw in get_keywords(chat_id):
            if kw.lower() in text.lower():
                return await issue_warn_or_mute(user_id, chat_id, message, f"ключевое слово «{kw}»")


def register_handlers_filter(dp):
    dp.include_router(router)
