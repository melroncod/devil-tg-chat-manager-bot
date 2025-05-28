import asyncio

from aiogram import Router, F, Bot, exceptions
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ChatMemberUpdated
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.chat_member_updated import (
    ChatMemberUpdatedFilter,
    JOIN_TRANSITION,
    LEAVE_TRANSITION,
)

from loader import bot
from db import (
    get_user_chats,
    remove_user_chat, add_user_chat,
    get_link_filter, set_link_filter,
    get_caps_filter, set_caps_filter,
    get_spam_filter, set_spam_filter,
    get_swear_filter, set_swear_filter,
    get_keywords_filter, set_keywords_filter,
    get_sticker_filter, set_sticker_filter,
    set_welcome_message, get_welcome_message,
    set_rules, get_rules,
    get_log_settings, set_log_chat,
    update_log_status, get_welcome_delete_timeout,
    get_join_delete, set_join_delete,
)
from services.logger import send_log
from handlers.start import inline_kb, reply_kb

router = Router()
WELCOME_DELETE_DEFAULT = 60


class WelcomeStates(StatesGroup):
    waiting_for_welcome = State()


class RulesStates(StatesGroup):
    waiting_for_rules = State()


class LoggingStates(StatesGroup):
    waiting_for_log_chat_id = State()


async def is_admin_in_chat(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception:
        return False


@router.message(F.text.lower() == "мои чаты", F.chat.type == ChatType.PRIVATE)
async def cmd_my_chats(message: Message):
    user_id = message.from_user.id
    uc = get_user_chats(user_id)
    if not uc:
        return await message.answer(
            "У вас ещё нет чатов. Добавьте через команду «Установка».",
            parse_mode="Markdown"
        )

    valid = {}
    for chat_id, name in uc.items():
        try:
            await bot.get_chat(chat_id)
            valid[chat_id] = name
        except (exceptions.TelegramForbiddenError, exceptions.TelegramBadRequest):
            remove_user_chat(user_id, chat_id)

    if not valid:
        return await message.answer(
            "У вас не осталось доступных чатов (бот был удалён).",
            parse_mode="Markdown"
        )

    buttons = [
                  [InlineKeyboardButton(text=name, callback_data=f"manage_uc:{chat_id}")]
                  for chat_id, name in valid.items()
              ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Ваши чаты:", reply_markup=kb)


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_bot_added(event: ChatMemberUpdated):
    me = await bot.get_me()
    if event.new_chat_member.user.id != me.id:
        return

    inviter = event.from_user
    if inviter is None:
        return

    chat = event.chat
    chat_id = chat.id
    chat_title = chat.title or str(chat_id)
    inviter_id = inviter.id

    try:
        member = await bot.get_chat_member(chat_id, inviter_id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
            return
    except Exception:
        return

    add_user_chat(inviter_id, chat_id, chat_title)

    try:
        await bot.send_message(
            inviter_id,
            f"✅ Чат «{chat_title}» (ID {chat_id}) успешно добавлен в ваши «Мои чаты»."
        )
    except exceptions.TelegramForbiddenError:
        pass


@router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(cq: CallbackQuery):
    await bot.send_message(
        cq.from_user.id,
        "Выберите действие:",
        reply_markup=reply_kb
    )
    await cq.answer()


@router.callback_query(F.data.startswith("manage_uc:"))
async def callback_manage_uc(cq: CallbackQuery):
    chat_id = int(cq.data.split(":", 1)[1])

    try:
        target_chat = await bot.get_chat(chat_id)
        chat_title = target_chat.title or target_chat.username or str(chat_id)
    except (exceptions.TelegramForbiddenError, exceptions.TelegramBadRequest):
        remove_user_chat(cq.from_user.id, chat_id)
        await cq.answer()
        return await callback_back_to_chats(cq)

    links_state = get_link_filter(chat_id)
    caps_state = get_caps_filter(chat_id)
    spam_state = get_spam_filter(chat_id)
    sticker_state = get_sticker_filter(chat_id)
    swear_state = get_swear_filter(chat_id)
    keywords_state = get_keywords_filter(chat_id)

    links_btn_text = f"🔗 Фильтрация ссылок: {'Вкл' if links_state else 'Выкл'}"
    caps_btn_text = f"🔠 Антикапс: {'Вкл' if caps_state else 'Выкл'}"
    spam_btn_text = f"🛡️ Антиспам: {'Вкл' if spam_state else 'Выкл'}"
    stickers_btn_text = f"⭐ Анти-стикеры: {'Вкл' if sticker_state else 'Выкл'}"
    swear_btn_text = f"🤬 Фильтрация мата: {'Вкл' if swear_state else 'Выкл'}"
    keywords_btn_text = f"🔑 Ключевые слова: {'Вкл' if keywords_state else 'Выкл'}"

    settings = get_log_settings(chat_id) or {}
    log_chat_id = settings.get("log_chat_id")
    logging_enabled = settings.get("is_logging_enabled", False)

    if log_chat_id:
        try:
            log_chat = await bot.get_chat(log_chat_id)
            log_title = log_chat.title or log_chat.username or str(log_chat_id)
        except Exception:
            log_title = str(log_chat_id)
    else:
        log_title = None

    log_btn_text = (
        f"🔔 Логирование: Вкл ({log_title})"
        if logging_enabled and log_title
        else "🔕 Логирование: Выкл"
    )

    join_enabled = get_join_delete(chat_id)
    join_btn_text = (
        "🗑️ Авто-удаление Join/Leave: Вкл"
        if join_enabled
        else "❌ Авто-удаление Join/Leave: Выкл"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=links_btn_text, callback_data=f"filter_links:{chat_id}")],
        [InlineKeyboardButton(text=caps_btn_text, callback_data=f"filter_caps:{chat_id}")],
        [InlineKeyboardButton(text=spam_btn_text, callback_data=f"filter_spam:{chat_id}")],
        [InlineKeyboardButton(text=stickers_btn_text, callback_data=f"filter_stickers:{chat_id}")],
        [InlineKeyboardButton(text=swear_btn_text, callback_data=f"filter_swear:{chat_id}")],
        [InlineKeyboardButton(text=keywords_btn_text, callback_data=f"filter_keywords:{chat_id}")],
        [InlineKeyboardButton(text="💬 Установка приветствия", callback_data=f"setup_welcome:{chat_id}")],
        [InlineKeyboardButton(text="📜 Установка правил", callback_data=f"setup_rules:{chat_id}")],
        [InlineKeyboardButton(text=log_btn_text, callback_data=f"logging:{chat_id}")],
        [InlineKeyboardButton(text=join_btn_text, callback_data=f"toggle_join_delete:{chat_id}")],
        [InlineKeyboardButton(text="❌ Удалить чат", callback_data=f"delete_chat:{chat_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_chats")],
    ])

    await cq.message.edit_text(
        f"Что настроить в чате <b>{chat_title}</b>?",
        parse_mode="HTML",
        reply_markup=kb
    )
    await cq.answer()


async def _get_chat_name(bot: Bot, chat_id: int) -> str:
    try:
        chat = await bot.get_chat(chat_id)
        return getattr(chat, "title", None) or f"ID {chat_id}"
    except Exception:
        return f"ID {chat_id}"


def _make_filter_handler(get_fn, set_fn, label: str):
    async def handler(cq: CallbackQuery):
        chat_id = int(cq.data.split(":", 1)[1])
        current = get_fn(chat_id)
        new_state = not current
        set_fn(chat_id, new_state)

        await cq.answer()
        await callback_manage_uc(cq)

        # логируем изменение фильтра
        chat_name = await _get_chat_name(bot, chat_id)
        await send_log(
            bot, chat_id,
            f"{'✅ Включен' if new_state else '❌ Отключен'} {label} "
            f"админом {cq.from_user.full_name} в «{chat_name}»"
        )

    return handler


# Регистрация фильтров с логированием
router.callback_query(F.data.startswith("filter_links:"))(
    _make_filter_handler(get_link_filter, set_link_filter, "фильтр ссылок")
)
router.callback_query(F.data.startswith("filter_caps:"))(
    _make_filter_handler(get_caps_filter, set_caps_filter, "антикапс")
)
router.callback_query(F.data.startswith("filter_spam:"))(
    _make_filter_handler(get_spam_filter, set_spam_filter, "антиспам")
)
router.callback_query(F.data.startswith("filter_stickers:"))(
    _make_filter_handler(get_sticker_filter, set_sticker_filter, "анти-стикеры")
)
router.callback_query(F.data.startswith("filter_swear:"))(
    _make_filter_handler(get_swear_filter, set_swear_filter, "фильтрацию мата")
)
router.callback_query(F.data.startswith("filter_keywords:"))(
    _make_filter_handler(get_keywords_filter, set_keywords_filter, "ключевые слова")
)


@router.callback_query(F.data.startswith("logging:"))
async def callback_logging(cq: CallbackQuery, state: FSMContext):
    chat_id = int(cq.data.split(":", 1)[1])
    settings = get_log_settings(chat_id) or {}
    log_id = settings.get("log_chat_id")
    enabled = settings.get("is_logging_enabled", False)

    if not log_id:
        await cq.message.answer("📥 Введите ID чата для логирования.", parse_mode="HTML")
        await state.update_data(chat_id=chat_id)
        await state.set_state(LoggingStates.waiting_for_log_chat_id)
        return await cq.answer()

    if not enabled:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, сменить", callback_data=f"logging_change:yes:{chat_id}"),
                InlineKeyboardButton(text="Нет, оставить", callback_data=f"logging_change:no:{chat_id}")
            ]
        ])
        await cq.message.answer("Хотите сменить чат для логирования?", reply_markup=kb)
        return await cq.answer()

    update_log_status(chat_id, False)
    await cq.answer()
    await callback_manage_uc(cq)

    # логируем отключение логирования
    chat_name = await _get_chat_name(bot, chat_id)
    await send_log(
        bot, chat_id,
        f"🔕 Логирование отключено админом {cq.from_user.full_name} в «{chat_name}»"
    )


@router.callback_query(F.data.startswith("logging_change:"))
async def callback_logging_change(cq: CallbackQuery, state: FSMContext):
    _, ans, chat_id_str = cq.data.split(":")
    chat_id = int(chat_id_str)

    if ans == "yes":
        await cq.message.answer("📥 Введите новый ID чата для логирования.", parse_mode="HTML")
        await state.update_data(chat_id=chat_id)
        await state.set_state(LoggingStates.waiting_for_log_chat_id)
    else:
        update_log_status(chat_id, True)
        await cq.answer()
        await callback_manage_uc(cq)

        # логируем повторное включение без смены чата
        chat_name = await _get_chat_name(bot, chat_id)
        await send_log(
            bot, chat_id,
            f"🔔 Логирование оставлено включённым админом {cq.from_user.full_name} в «{chat_name}»"
        )


@router.message(LoggingStates.waiting_for_log_chat_id)
async def process_log_chat_id(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data["chat_id"]
    text = message.text.strip()
    chat_name = await _get_chat_name(bot, chat_id)

    if text.lower() == "off":
        update_log_status(chat_id, False)
        await message.answer("✅ Логирование отключено.")
        await send_log(
            bot, chat_id,
            f"🔕 Логирование отключено админом {message.from_user.full_name} в «{chat_name}»"
        )
    else:
        try:
            new_id = int(text)
            await bot.send_message(new_id, "✅ Логирование подключено.")
            set_log_chat(chat_id, new_id)
            update_log_status(chat_id, True)
            ch = await bot.get_chat(new_id)
            title = ch.title or ch.username or str(new_id)
            await message.answer(f"✅ Логирование подключено в чат: {title}")
            await send_log(
                bot, chat_id,
                f"🔔 Логирование включено админом {message.from_user.full_name} "
                f"и теперь идёт в «{title}» в чате «{chat_name}»"
            )
        except Exception as e:
            return await message.answer(f"❌ Не удалось установить лог-чат: {e}")

    await state.clear()
    fake = CallbackQuery(
        id=str(message.message_id),
        from_user=message.from_user,
        chat_instance="",
        message=message,
        data=f"manage_uc:{chat_id}"
    )
    await callback_manage_uc(fake)


@router.callback_query(F.data.startswith("toggle_join_delete:"))
async def callback_toggle_join_delete(cq: CallbackQuery):
    chat_id = int(cq.data.split(":", 1)[1])
    current = get_join_delete(chat_id)
    new_state = not current
    set_join_delete(chat_id, new_state)

    await cq.answer()
    await callback_manage_uc(cq)

    chat_name = (await bot.get_chat(chat_id)).title or str(chat_id)
    await send_log(
        bot, chat_id,
        f"🗑️ Авто-удаление Join/Leave сообщений "
        f"{'включено' if new_state else 'отключено'} "
        f"админом {cq.from_user.full_name} в «{chat_name}»"
    )


@router.callback_query(F.data.startswith("setup_welcome:"))
async def callback_setup_welcome(cq: CallbackQuery, state: FSMContext):
    chat_id = int(cq.data.split(":", 1)[1])
    if not await is_admin_in_chat(chat_id, cq.from_user.id):
        return await cq.answer("❌ Только админ может.", show_alert=True)

    current = get_welcome_message(chat_id)
    prompt = (
        f"🔧 Текущее приветствие:\n{current}\n\n"
        "Введите новый текст приветствия.\n"
        "Шаблоны: {first_name}, {username}, {chat_title}. HTML разрешен."
    ) if current else (
        "🔧 Приветствие ещё не задано.\n\n"
        "Введите текст приветствия.\n"
        "Шаблоны: {first_name}, {username}, {chat_title}. HTML разрешен."
    )

    await state.update_data(chat_id=chat_id)
    await cq.message.answer(prompt, parse_mode="HTML")
    await state.set_state(WelcomeStates.waiting_for_welcome)
    await cq.answer()


@router.message(WelcomeStates.waiting_for_welcome)
async def process_welcome_text(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data["chat_id"]
    text = message.text.strip()
    set_welcome_message(chat_id, text)

    await message.answer(f"✅ Приветствие установлено:\n\n{text}")
    chat_name = await _get_chat_name(bot, chat_id)
    await send_log(
        bot, chat_id,
        f"✏️ Приветствие изменено админом {message.from_user.full_name} "
        f"(@{message.from_user.username or '—'}) в чате «{chat_name}»:\n{text}"
    )
    await state.clear()


async def _delete_message_after(bot: Bot, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except exceptions.TelegramBadRequest:
        pass


@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_user_join(event: ChatMemberUpdated):
    if event.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    welcome = get_welcome_message(event.chat.id)
    user = event.new_chat_member.user

    if welcome:
        text = welcome.format(
            first_name=user.first_name or "",
            username=f"@{user.username}" if user.username else "",
            chat_title=event.chat.title
        )
        sent: Message = await bot.send_message(
            event.chat.id,
            text,
            parse_mode="HTML"
        )

        timeout = get_welcome_delete_timeout(event.chat.id) or WELCOME_DELETE_DEFAULT
        if timeout > 0:
            asyncio.create_task(
                _delete_message_after(bot, sent.chat.id, sent.message_id, timeout)
            )

    chat_name = event.chat.title or f"ID {event.chat.id}"
    await send_log(
        bot, event.chat.id,
        f"👤 Новый участник: {user.full_name} @{user.username or '—'} (#u{user.id}) "
        f"в чате «{chat_name}»"
    )


@router.chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def on_user_leave(event: ChatMemberUpdated):
    if event.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    user = event.old_chat_member.user
    chat_name = event.chat.title or f"ID {event.chat.id}"
    await send_log(
        bot, event.chat.id,
        f"🚪 Участник вышел: {user.full_name} @{user.username or '—'} "
        f"(#u{user.id}) из «{chat_name}»"
    )


@router.message(
    (F.new_chat_members.is_not(None) | F.left_chat_member.is_not(None)),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
)
async def delete_system_join_or_leave_message(message: Message):
    chat_id = message.chat.id
    if not get_join_delete(chat_id):
        return
    try:
        await message.delete()
    except (exceptions.TelegramForbiddenError, exceptions.TelegramBadRequest):
        pass


@router.callback_query(F.data.startswith("setup_rules:"))
async def callback_setup_rules(cq: CallbackQuery, state: FSMContext):
    chat_id = int(cq.data.split(":", 1)[1])
    if not await is_admin_in_chat(chat_id, cq.from_user.id):
        return await cq.answer("❌ Только админ может.")

    current = get_rules(chat_id) or "(не заданы)"
    await state.update_data(chat_id=chat_id)
    await cq.message.answer(f"🔧 Текущие правила:\n{current}\n\nВведите новые правила (HTML).")
    await state.set_state(RulesStates.waiting_for_rules)
    await cq.answer()


@router.message(RulesStates.waiting_for_rules)
async def process_rules_text(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data["chat_id"]
    text = message.text.strip()
    set_rules(chat_id, text)

    await message.answer(f"✅ Правила установлены:\n\n{text}")
    chat_name = await _get_chat_name(bot, chat_id)
    await send_log(
        bot, chat_id,
        f"✏️ Правила изменены админом {message.from_user.full_name} "
        f"(@{message.from_user.username or '—'}) в чате «{chat_name}»:\n{text}"
    )
    await state.clear()


@router.callback_query(F.data.startswith("delete_chat:"))
async def callback_delete_chat(cq: CallbackQuery):
    chat_id = int(cq.data.split(":", 1)[1])
    remove_user_chat(cq.from_user.id, chat_id)
    await cq.message.edit_text("Чат удалён из вашего списка.")
    await cq.answer()
    await send_log(
        bot, chat_id,
        f"🗑️ Чат удалён из списка пользователем {cq.from_user.full_name}"
    )


@router.callback_query(F.data == "back_to_chats")
async def callback_back_to_chats(cq: CallbackQuery):
    user_id = cq.from_user.id
    uc = get_user_chats(user_id)
    if not uc:
        await cq.message.edit_text(
            "У вас ещё нет чатов. Добавьте через команду «Установка».",
            parse_mode="Markdown"
        )
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=name, callback_data=f"manage_uc:{chat_id}")]
                for chat_id, name in uc.items()
            ]
        )
        await cq.message.edit_text("Ваши чаты:", reply_markup=kb)
    await cq.answer()


def register_handlers_user_chats(dp):
    dp.include_router(router)
