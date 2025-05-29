import logging
from time import time

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from loader import bot
from services.logger import send_log
from db import (
    upsert_alias,
    resolve_username,
    add_mute,
    reset_mutes,
    add_ban,
    reset_bans,
    reset_warns,
    reset_all_warns,
    add_user_chat,
    add_chat,
    set_rules,
    get_rules,
    set_welcome_delete_timeout,
    get_welcome_delete_timeout,
    get_keywords,
    add_keyword,
    remove_keyword,
    get_log_settings,
    get_devil_mode,
    set_devil_mode,
    get_admins,
)
from handlers.user_chats import callback_manage_uc

logger = logging.getLogger(__name__)
router = Router()
WELCOME_DELETE_DEFAULT = 60


async def is_chat_admin(message: types.Message) -> bool:
    if message.sender_chat:
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except:
        return False


async def _get_chat_name(chat_id: int) -> str:
    try:
        chat = await bot.get_chat(chat_id)
        return chat.title or str(chat_id)
    except:
        return str(chat_id)


async def get_target_user(message: types.Message, username: str | None = None) -> types.User | None:
    chat_id = message.chat.id
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        if target and target.username:
            upsert_alias(chat_id, target.username, target.id)
        return target
    if username:
        mention = username.lstrip('@').lower()
        target_id = resolve_username(chat_id, mention)
        if target_id:
            try:
                member = await bot.get_chat_member(chat_id, target_id)
                return member.user
            except:
                return None
        try:
            member = await bot.get_chat_member(chat_id, mention)
            user = member.user
            if user.username:
                upsert_alias(chat_id, user.username, user.id)
            return user
        except:
            return None
    return None


async def process_admin_command(message: types.Message, command_type: str) -> None:
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins():
        if not await is_chat_admin(message):
            await message.reply("❌ Только администраторы чата (или супер-админ бота) могут использовать эту команду.")
            return
    parts = message.text.split()
    username_arg = parts[1] if len(parts) > 1 else None
    target = await get_target_user(message, username_arg)
    if not target:
        await message.reply("❗ Ответьте на сообщение или укажите @username (или ID).")
        return
    chat_id = message.chat.id
    chat_name = await _get_chat_name(chat_id)
    target_id = target.id
    if target_id in get_admins():
        await message.reply("❗ Нельзя воздействовать на главного админа бота.")
        return
    try:
        member = await bot.get_chat_member(chat_id, target_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.reply("❗ Нельзя воздействовать на администратора группы.")
            return
    except:
        pass
    try:
        if command_type == "ban":
            await bot.ban_chat_member(chat_id, target_id)
            add_ban(target_id, chat_id, target.username or target.full_name)
            await message.reply(f"✅ @{target.username or target.first_name} забанен")
            await send_log(
                bot, chat_id,
                f"🔨 ban: @{target.username or target.first_name} (#{target_id}) забанен админом {message.from_user.full_name} в «{chat_name}»"
            )
        elif command_type == "unban":
            await bot.unban_chat_member(chat_id, target_id)
            reset_bans(target_id, chat_id)
            await message.reply(f"✅ @{target.username or target.first_name} разбанен")
            await send_log(
                bot, chat_id,
                f"🔓 unban: @{target.username or target.first_name} (#{target_id}) разбанен админом {message.from_user.full_name} в «{chat_name}»"
            )
        elif command_type == "mute":
            restriction = 300
            if len(parts) > 2:
                try:
                    restriction = int(parts[2]) * 3600
                except ValueError:
                    await message.reply("❗ Неверный формат времени. Укажите число часов.")
                    return
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=target_id,
                permissions=types.ChatPermissions(can_send_messages=False),
                until_date=int(time()) + restriction
            )
            add_mute(target_id, chat_id, target.username or target.full_name)
            period = f"{parts[2]} ч" if len(parts) > 2 else "навсегда"
            await message.reply(f"✅ @{target.username or target.first_name} замучен {period}")
            await send_log(
                bot, chat_id,
                f"🔇 mute: @{target.username or target.first_name} (#{target_id}) замучен {period} админом {message.from_user.full_name} в «{chat_name}»"
            )
        elif command_type == "unmute":
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=target_id,
                permissions=types.ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            reset_mutes(target_id, chat_id)
            await message.reply(f"✅ @{target.username or target.first_name} размучен")
            await send_log(
                bot, chat_id,
                f"🔊 unmute: @{target.username or target.first_name} (#{target_id}) размучен админом {message.from_user.full_name} в «{chat_name}»"
            )
    except Exception as e:
        logger.error(f"Ошибка в process_admin_command: {e}")
        await message.reply(f"❗ Произошла ошибка: {e}")


PREFIXES = ("/", "!")


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
    Command(commands=["ro"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_ro(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    chat_id = message.chat.id
    chat_name = await _get_chat_name(chat_id)
    chat = await bot.get_chat(chat_id)
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
    await bot.set_chat_permissions(chat_id=chat_id, permissions=perms)
    await message.reply(f"✅ Read-Only режим {status}")
    await send_log(
        bot, chat_id,
        f"👁️ ro: режим чтения {status} админом {message.from_user.full_name} в «{chat_name}»"
    )


@router.message(
    Command(commands=["resetwarn"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_resetwarn(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    target = await get_target_user(message)
    if not target:
        return
    reset_warns(target.id, message.chat.id)
    chat_id = message.chat.id
    chat_name = await _get_chat_name(chat_id)
    display = target.username or target.full_name
    await message.reply(f"✅ Варны @{display} обнулены")
    await send_log(
        bot, message.chat.id,
        f"♻️ resetwarn: @{display} (#{target.id}) обнулены админом {message.from_user.full_name} в «{chat_name}»"
    )


@router.message(
    Command(commands=["resetwarnsall"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_resetwarnsall(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    try:
        reset_all_warns(message.chat.id)
        chat_id = message.chat.id
        chat_name = await _get_chat_name(chat_id)
        await message.reply("✅ Все варны сброшены")
        await send_log(
            bot, message.chat.id,
            f"♻️ resetwarnsall: все варны сброшены админом {message.from_user.full_name} в «{chat_name}»"
        )
    except:
        return


@router.message(
    Command(commands=["setup"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_setup(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    chat_id = message.chat.id
    chat_title = message.chat.title or f"chat_{chat_id}"
    add_chat(chat_id, chat_title)
    chat_name = await _get_chat_name(chat_id)
    add_user_chat(sender_id, chat_id, chat_title)
    await message.reply(f"✅ Чат «{chat_title}» зарегистрирован")
    await send_log(
        bot, chat_id,
        f"🛠️ setup: чат «{chat_title}» зарегистрирован пользователем {message.from_user.full_name} в «{chat_name}»"
    )


@router.message(
    Command(commands=["rules"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_show_rules(message: types.Message):
    chat_id = message.chat.id
    rules = get_rules(chat_id)
    if not rules:
        await message.reply("❗ Правила ещё не заданы.")
    else:
        await message.reply(f"📜 <b>Правила чата:</b>\n{rules}", parse_mode="HTML")


@router.message(
    Command(commands=["setwelcomedelete"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_set_welcome_delete(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    try:
        t = int(parts[1])
        if t < 0:
            return
    except:
        return
    set_welcome_delete_timeout(message.chat.id, t)
    chat_id = message.chat.id
    chat_name = await _get_chat_name(chat_id)
    text = "отключено" if t == 0 else f"{t} сек"
    await message.reply(f"✅ Авто-удаление приветствия {text}")
    await send_log(
        bot, message.chat.id,
        f"⏱️ setwelcomedelete: {text} админом {message.from_user.full_name} в «{chat_name}»"
    )


@router.message(
    Command(commands=["getwelcomedelete"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_get_welcome_delete(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    t = get_welcome_delete_timeout(message.chat.id)
    if t is None:
        t = WELCOME_DELETE_DEFAULT
        await message.reply(f"Дефолт: {t} сек.")
    elif t == 0:
        await message.reply("Авто-удаление отключено.")
    else:
        await message.reply(f"Авто-удаление: {t} сек.")


@router.message(
    Command(commands=["setkw"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_add_keyword(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return
    kw = parts[1].strip().lower()
    add_keyword(message.chat.id, kw)
    chat_id = message.chat.id
    chat_name = await _get_chat_name(chat_id)
    await message.reply(f"✅ Ключевое слово «{kw}» добавлено")
    await send_log(
        bot, message.chat.id,
        f"🔑 setkw: «{kw}» добавлено админом {message.from_user.full_name} в «{chat_name}»"
    )


@router.message(
    Command(commands=["remfromkw"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_remove_keyword(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return
    kw = parts[1].strip().lower()
    remove_keyword(message.chat.id, kw)
    chat_id = message.chat.id
    chat_name = await _get_chat_name(chat_id)
    await message.reply(f"✅ Ключевое слово «{kw}» удалено")
    await send_log(
        bot, message.chat.id,
        f"❌ remfromkw: «{kw}» удалено админом {message.from_user.full_name} в «{chat_name}»"
    )


@router.message(
    Command(commands=["demon"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_demon_text(message: Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    chat_id = message.chat.id
    set_devil_mode(chat_id, True)
    await message.reply("👿 <b>Devil mode</b> включён! С этого момента разрешены <b>только</b> сообщения с матами.")
    chat_name = await _get_chat_name(chat_id)
    await send_log(
        bot, chat_id,
        f"👿 demon: Devil mode включён админом {message.from_user.full_name} в «{chat_name}»"
    )
    fake = CallbackQuery(
        id=str(message.message_id),
        from_user=message.from_user,
        chat_instance="",
        message=message,
        data=f"manage_uc:{chat_id}"
    )
    try:
        await callback_manage_uc(fake)
    except TelegramBadRequest:
        return


@router.message(
    Command(commands=["demoff"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_demoff_text(message: Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins() and not await is_chat_admin(message):
        return
    chat_id = message.chat.id
    set_devil_mode(chat_id, False)
    await message.reply("😈 <b>Devil mode</b> отключён. Возвращаемся к <b>обычным</b> правилам.")
    chat_name = await _get_chat_name(chat_id)
    await send_log(
        bot, chat_id,
        f"😈 demoff: Devil mode отключён админом {message.from_user.full_name} в «{chat_name}»"
    )
    fake = CallbackQuery(
        id=str(message.message_id),
        from_user=message.from_user,
        chat_instance="",
        message=message,
        data=f"manage_uc:{chat_id}"
    )
    try:
        await callback_manage_uc(fake)
    except TelegramBadRequest:
        return


@router.message(
    Command(commands=["listkw"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_list_keywords(message: Message):
    kws = get_keywords(message.chat.id)
    if not kws:
        return
    await message.reply("🔑 Keywords:\n" + "\n".join(f"- {w}" for w in kws))


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
        "/setwelcomedelete [секунд] — задать таймаут авто-удаления приветствия\n"
        "/getwelcomedelete — показать текущую настройку авто-удаления\n"
        "/setkw [слово] — добавить ключевое слово в фильтр\n"
        "/remfromkw [слово] — удалить ключевое слово из фильтра\n"
        "/listkw — показать все ключевые слова\n"
        "/demon — включить Devil mode (только с матами)\n"
        "/demoff — выключить Devil mode"
    )
    await message.reply(help_text, parse_mode="Markdown")


@router.message(
    Command(commands=["msg"], prefix=PREFIXES, ignore_mention=True, ignore_case=True),
    F.chat.type.in_([ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP])
)
async def cmd_msg(message: types.Message):
    sender_id = message.from_user.id if message.from_user else None
    if sender_id not in get_admins():
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply("❗ Использование: !msg <chat_id> <текст>")
        return
    try:
        target_chat = int(parts[1])
    except ValueError:
        await message.reply("❗ Неверный chat_id")
        return
    text = parts[2]
    try:
        await bot.send_message(chat_id=target_chat, text=text)
        await message.reply("✅ Сообщение отправлено")
    except TelegramBadRequest as e:
        await message.reply(f"❗ Ошибка при отправке: {e}")


def register_handlers_aliases(dp):
    dp.include_router(router)
