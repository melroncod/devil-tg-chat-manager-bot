import logging
from aiogram.types import Message
import sqlite3
from time import time
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums import ChatType, ChatMemberStatus
from loader import bot
from db import (
    DB_NAME,
    upsert_alias, resolve_username,
    add_mute, reset_mutes,
    add_ban, reset_bans,
    reset_warns,
    add_user_chat, add_chat,
    set_rules, get_rules,
    set_welcome_delete_timeout, get_welcome_delete_timeout,
    get_keywords, add_keyword, remove_keyword
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

WELCOME_DELETE_DEFAULT = 60

async def is_chat_admin(message: types.Message) -> bool:
    """
    Проверяем, является ли отправитель администратором или создателем чата
    """
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception as e:
        logger.error(f"Ошибка при проверке прав админа: {e}")
        return False

async def get_target_user(message: types.Message, username: str | None = None) -> types.User | None:
    chat_id = message.chat.id
    # Ответом на сообщение
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        if target.username:
            upsert_alias(chat_id, target.username, target.id)
        return target
    # Аргумент username или ID
    if username:
        target_id = resolve_username(chat_id, username.lstrip('@').lower())
        if target_id:
            try:
                member = await bot.get_chat_member(chat_id, target_id)
                return member.user
            except Exception:
                pass
        try:
            member = await bot.get_chat_member(chat_id, username)
            if member.user.username:
                upsert_alias(chat_id, member.user.username, member.user.id)
            return member.user
        except Exception:
            return None
    return None

async def process_admin_command(message: types.Message, command_type: str) -> None:
    logger.info(f"Process command {command_type} by {message.from_user.id}: {message.text}")
    # Проверка прав в чате
    if not await is_chat_admin(message):
        await message.reply("❌ Только администраторы чата могут использовать эту команду")
        return
    parts = message.text.split()
    username_arg = parts[1] if len(parts) > 1 else None
    target = await get_target_user(message, username_arg)
    if not target:
        await message.reply("❗ Ответьте на сообщение или укажите @username (или ID)")
        return
    try:
        member = await bot.get_chat_member(message.chat.id, target.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.reply("❗ Нельзя воздействовать на администратора")
            return
        # BAN / UNBAN
        if command_type == "ban":
            await bot.ban_chat_member(message.chat.id, target.id)
            add_ban(target.id, message.chat.id, target.username or target.full_name)
            await message.reply(f"✅ Пользователь @{target.username or target.first_name} забанен")
        elif command_type == "unban":
            await bot.unban_chat_member(message.chat.id, target.id)
            reset_bans(target.id, message.chat.id)
            await message.reply(f"✅ Пользователь @{target.username or target.first_name} разбанен")
        # MUTE / UNMUTE
        elif command_type == "mute":
            restriction = 300
            if len(parts) > 2:
                try:
                    restriction = int(parts[2]) * 3600
                except ValueError:
                    await message.reply("❗ Неверный формат времени. Укажите число часов.")
                    return
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target.id,
                permissions=types.ChatPermissions(),
                until_date=int(time()) + restriction
            )
            add_mute(target.id, message.chat.id, target.username or target.full_name)
            period = f"на {parts[2]} часов" if len(parts) > 2 else "навсегда"
            await message.reply(f"✅ Пользователь @{target.username or target.first_name} замучен {period}")
        elif command_type == "unmute":
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target.id,
                permissions=types.ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            reset_mutes(target.id, message.chat.id)
            await message.reply(f"✅ Пользователь @{target.username or target.first_name} размучен")
    except Exception as e:
        logger.error(f"Ошибка в process_admin_command: {e}")
        await message.reply(f"❗ Произошла ошибка: {e}")

# Префиксы команд
PREFIXES = ("/", "!")

# Существующие хэндлеры ban, unban, mute, unmute, checkperms, ro
@router.message(
    Command(commands=["ban", "бан"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_ban(message: types.Message):
    await process_admin_command(message, "ban")

@router.message(
    Command(commands=["unban"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_unban(message: types.Message):
    await process_admin_command(message, "unban")

@router.message(
    Command(commands=["mute"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_mute(message: types.Message):
    await process_admin_command(message, "mute")

@router.message(
    Command(commands=["unmute"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_unmute(message: types.Message):
    await process_admin_command(message, "unmute")

@router.message(
    Command(commands=["checkperms"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_checkperms(message: types.Message):
    if not await is_chat_admin(message):
        await message.reply("❌ Только администраторы чата могут использовать эту команду")
        return
    target = await get_target_user(message)
    if not target:
        await message.reply("❗ Ответьте на сообщение пользователя")
        return
    try:
        member = await bot.get_chat_member(message.chat.id, target.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.reply("❗ Администраторы имеют все права")
            return
        text = (
            "🔹 Права пользователя:"
            f"\nОтправлять сообщения: {'✅' if member.can_send_messages else '❌'}"
            f"\nОтправлять медиа: {'✅' if member.can_send_media_messages else '❌'}"
            f"\nОтправлять стикеры/открытки: {'✅' if member.can_send_other_messages else '❌'}"
            f"\nДобавлять превью: {'✅' if member.can_add_web_page_previews else '❌'}"
        )
        await message.reply(text)
    except Exception as e:
        logger.error(f"Ошибка в checkperms: {e}")
        await message.reply(f"❗ Произошла ошибка: {e}")

@router.message(
    Command(commands=["ro"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_ro(message: types.Message):
    if not await is_chat_admin(message):
        await message.reply("❌ Только администраторы чата могут использовать эту команду")
        return
    chat = await bot.get_chat(message.chat.id)
    current = chat.permissions or types.ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    ro_enabled = not current.can_send_messages
    perms = types.ChatPermissions(
        can_send_messages=ro_enabled,
        can_send_media_messages=ro_enabled,
        can_send_other_messages=ro_enabled,
        can_add_web_page_previews=ro_enabled
    )
    status = "выключен" if ro_enabled else "включен"
    await bot.set_chat_permissions(chat_id=message.chat.id, permissions=perms)
    await message.reply(f"✅ Read-Only режим {status}")

# Новые хэндлеры для сброса варнов
@router.message(
    Command(commands=["resetwarn"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_resetwarn(message: types.Message):
    if not await is_chat_admin(message):
        return await message.reply("❌ Только администраторы чата могут использовать эту команду")
    target = await get_target_user(message)
    if not target:
        return await message.reply("❗ Ответьте reply на сообщение нарушителя или укажите @username")
    reset_warns(target.id, message.chat.id)
    display = target.username or target.full_name
    await message.reply(f"✅ Варны пользователя @{display} обнулены")

@router.message(
    Command(commands=["resetwarnsall"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_resetwarnsall(message: types.Message):
    if not await is_chat_admin(message):
        return await message.reply("❌ Только администраторы чата могут использовать эту команду")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM warnings WHERE chat_id = ?", (message.chat.id,))
    conn.commit()
    conn.close()
    await message.reply("✅ Все варны в этом чате сброшены")


@router.message(
    Command(commands=["setup"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_setup(message: Message):
    """
    Регистрирует чат и добавляет связь пользователь–чат для команды !setup
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_title = message.chat.title or f"chat_{chat_id}"
    # Добавляем сам чат в базу (если ещё нет)
    add_chat(chat_id, chat_title)
    # Добавляем связь «пользователь — чат», теперь с указанием названия
    add_user_chat(user_id, chat_id, chat_title)
    await message.reply(f"✅ Чат «{chat_title}» зарегистрирован и добавлен в ваш список «Мои чаты»")

# 7) Вывод правил командой /rules или !rules
@router.message(
    Command(commands=["rules"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_show_rules(message: Message):
    chat_id = message.chat.id
    rules = get_rules(chat_id)
    if not rules:
        await message.reply("❗ Правила для этого чата ещё не заданы.")
    else:
        await message.reply(f"📜 <b>Правила чата:</b>\n{rules}", parse_mode="HTML")

# /setwelcomedelete <секунд> — задаёт таймаут авто‑удаления
@router.message(
    Command(commands=["setwelcomedelete"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_set_welcome_delete(message: Message):
    if not await is_chat_admin(message):
        return await message.reply("❌ Только администраторы могут.")
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply("❗ Укажите время в секундах (0 — отключить).")
    try:
        t = int(parts[1])
        if t < 0:
            raise ValueError
    except ValueError:
        return await message.reply("❗ Неверный формат. Нужно целое число ≥ 0.")
    set_welcome_delete_timeout(message.chat.id, t)
    if t == 0:
        await message.reply("✅ Авто‑удаление приветствия отключено.")
    else:
        await message.reply(f"✅ Авто‑удаление приветствия установлено: {t} секунд.")

# /getwelcomedelete — показывает текущую настройку
@router.message(
    Command(commands=["getwelcomedelete"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_get_welcome_delete(message: Message):
    if not await is_chat_admin(message):
        return await message.reply("❌ Только администраторы могут.")
    t = get_welcome_delete_timeout(message.chat.id)
    if t is None:
        t = WELCOME_DELETE_DEFAULT
        await message.reply(f"Таймаут не задан, используется дефолт: {t} секунд.")
    elif t == 0:
        await message.reply("Авто‑удаление приветствия **отключено**.")
    else:
        await message.reply(f"Авто‑удаление приветствия: {t} секунд.")


@router.message(
    Command(commands=["setkw"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_add_keyword(message: Message):
    if not await is_chat_admin(message):
        return await message.reply("❌ Только администратор может добавлять ключевые слова.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await message.reply("❗ Укажите ключевое слово после команды.\nПример: `/setkw спойлер`", parse_mode="Markdown")
    kw = parts[1].strip().lower()
    add_keyword(message.chat.id, kw)
    await message.reply(f"✅ Ключевое слово «{kw}» добавлено в фильтр.")

# Удалить ключевое слово из фильтра: /nor спойлер
@router.message(
    Command(commands=["remfromkw"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_remove_keyword(message: Message):
    if not await is_chat_admin(message):
        return await message.reply("❌ Только администратор может удалять ключевые слова.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await message.reply("❗ Укажите ключевое слово для удаления.\nПример: `/remfromkw спойлер`", parse_mode="Markdown")
    kw = parts[1].strip().lower()
    remove_keyword(message.chat.id, kw)
    await message.reply(f"✅ Ключевое слово «{kw}» удалено из фильтра.")

# Показать текущие ключевые слова: /listkw
@router.message(
    Command(commands=["listkw"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_list_keywords(message: Message):
    kws = get_keywords(message.chat.id)
    if not kws:
        return await message.reply("⚠️ Пока нет ни одного ключевого слова.")
    await message.reply("🔑 Текущие ключевые слова в фильтре:\n" +
                        "\n".join(f"- {w}" for w in kws))


@router.message(
    Command(commands=["help", "commands"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_show_commands(message: Message):
    help_text = (
        "/rules — показать правила чата\n"
        "/setup — регистрация чата для управления\n"
        "/ban [@username|reply] — забанить пользователя\n"
        "/unban [@username|reply] — разбанить пользователя\n"
        "/mute [@username|reply] [часы] — замутить пользователя\n"
        "/unmute [@username|reply] — размутить пользователя\n"
        "/checkperms [@username|reply] — проверить права пользователя\n"
        "/ro — переключить режим только для чтения\n"
        "/resetwarn [@username|reply] — обнулить варны пользователя\n"
        "/resetwarnsall — обнулить все варны в чате\n"
        "/setwelcomedelete [секунд] — задать таймаут авто‑удаления приветствия\n"
        "/getwelcomedelete — показать текущую настройку авто‑удаления\n"
        "/setkw [слово] — добавить ключевое слово в фильтр\n"
        "/remfromkw [слово] — удалить ключевое слово из фильтра\n"
        "/listkw — показать все ключевые слова"
    )
    # Отправляем как Markdown, чтобы угловые скобки не ломали парсер HTML
    await message.reply(help_text, parse_mode="Markdown")


def register_handlers_aliases(dp):
    dp.include_router(router)
