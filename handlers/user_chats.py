# user_chats.py

from aiogram import Router, F, Bot
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ChatMemberUpdated
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION

from loader import bot
from db import (
    get_user_chats,
    remove_user_chat,
    get_link_filter,    set_link_filter,
    get_caps_filter,    set_caps_filter,
    get_spam_filter,    set_spam_filter,
    get_swear_filter,   set_swear_filter,
    get_keywords_filter,set_keywords_filter,
    set_welcome_message, get_welcome_message,
    set_rules,          get_rules,
    get_sticker_filter, set_sticker_filter,
    get_log_settings,   set_log_chat,
    update_log_status
)
from services.logger import send_log

router = Router()

# --- FSM для Welcome, Rules и Logging ---
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


# 1) Мои чаты (приват)
@router.message(F.text.lower() == "мои чаты", F.chat.type == ChatType.PRIVATE)
async def cmd_my_chats(message: Message):
    user_id = message.from_user.id
    uc = get_user_chats(user_id)
    if not uc:
        return await message.answer(
            "У вас ещё нет чатов. Добавьте через команду «установка»",
            parse_mode="Markdown"
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"manage_uc:{chat_id}")]
            for chat_id, name in uc.items()
        ]
    )
    await message.answer("Ваши чаты:", reply_markup=kb)


# 2) Главное меню управления выбранным чатом
@router.callback_query(F.data.startswith("manage_uc:"))
async def callback_manage_uc(cq: CallbackQuery):
    chat_id = int(cq.data.split(":", 1)[1])

    # Сначала получаем название самого управляемого чата
    try:
        target_chat = await bot.get_chat(chat_id)
        chat_title = target_chat.title or target_chat.username or str(chat_id)
    except Exception:
        chat_title = str(chat_id)

    # Дальше собираем настройки логирования
    settings = get_log_settings(chat_id) or {}
    log_chat_id = settings.get("log_chat_id")
    logging_enabled = settings.get("is_logging_enabled", False)

    # Получаем название канала для логов (если есть)
    if log_chat_id:
        try:
            log_chat = await bot.get_chat(log_chat_id)
            log_title = log_chat.title or log_chat.username or str(log_chat_id)
        except Exception:
            log_title = str(log_chat_id)
    else:
        log_title = None

    # Собираем текст кнопки логирования
    if logging_enabled and log_title:
        log_btn_text = f"🔔 Логирование: Вкл ({log_title})"
    else:
        log_btn_text = "🔕 Логирование: Выкл"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фильтрация ссылок",     callback_data=f"filter_links:{chat_id}")],
        [InlineKeyboardButton(text="Антикапс",              callback_data=f"filter_caps:{chat_id}")],
        [InlineKeyboardButton(text="Антиспам",              callback_data=f"filter_spam:{chat_id}")],
        [InlineKeyboardButton(text="Антиспам стикеров",     callback_data=f"filter_stickers:{chat_id}")],
        [InlineKeyboardButton(text="Фильтрация мата",       callback_data=f"filter_swear:{chat_id}")],
        [InlineKeyboardButton(text="Ключевые слова",        callback_data=f"filter_keywords:{chat_id}")],
        [InlineKeyboardButton(text="Установка приветствия", callback_data=f"setup_welcome:{chat_id}")],
        [InlineKeyboardButton(text="Установка правил",      callback_data=f"setup_rules:{chat_id}")],
        [InlineKeyboardButton(text=log_btn_text,            callback_data=f"logging:{chat_id}")],
        [InlineKeyboardButton(text="❌ Удалить чат",         callback_data=f"delete_chat:{chat_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_chats")],
    ], row_width=1)

    await cq.message.edit_text(
        f"Что настроить в чате <b>{chat_title}</b>?",
        parse_mode="HTML",
        reply_markup=kb
    )
    await cq.answer()


# 3) Переключаем фильтры с логированием
def _make_filter_handler(prefix: str, get_fn, set_fn, on_text: str, off_text: str):
    async def handler(cq: CallbackQuery):
        chat_id = int(cq.data.split(":", 1)[1])
        cur = get_fn(chat_id)
        new = not cur
        set_fn(chat_id, new)
        await cq.answer(f"{prefix} {'✅ ' + on_text if new else '❌ ' + off_text}", show_alert=True)
        await send_log(
            bot, chat_id,
            f"⚙️ {prefix} {'включено' if new else 'отключено'} админом "
            f"{cq.from_user.full_name} (@{cq.from_user.username or '—'})"
        )
    return handler

router.callback_query(F.data.startswith("filter_links:"))( 
    _make_filter_handler("Фильтрация ссылок",
                         get_link_filter, set_link_filter,
                         "Включена", "Выключена") )
router.callback_query(F.data.startswith("filter_caps:"))(
    _make_filter_handler("Антикапс",
                         get_caps_filter, set_caps_filter,
                         "Включён", "Выключён") )
router.callback_query(F.data.startswith("filter_spam:"))(
    _make_filter_handler("Антиспам",
                         get_spam_filter, set_spam_filter,
                         "Включён", "Выключён") )
router.callback_query(F.data.startswith("filter_stickers:"))(
    _make_filter_handler("Антиспам стикеров",
                         get_sticker_filter, set_sticker_filter,
                         "Включён", "Выключён") )
router.callback_query(F.data.startswith("filter_swear:"))(
    _make_filter_handler("Фильтрация мата",
                         get_swear_filter, set_swear_filter,
                         "Включена", "Выключена") )
router.callback_query(F.data.startswith("filter_keywords:"))(
    _make_filter_handler("Ключевые слова",
                         get_keywords_filter, set_keywords_filter,
                         "Включены", "Выключены") )


# 4) Установка приветствия
@router.callback_query(F.data.startswith("setup_welcome:"))
async def callback_setup_welcome(cq: CallbackQuery, state: FSMContext):
    chat_id = int(cq.data.split(":",1)[1])
    if not await is_admin_in_chat(chat_id, cq.from_user.id):
        return await cq.answer("❌ Только админ может.", show_alert=True)
    await state.update_data(chat_id=chat_id)
    await cq.message.answer(
        "🔧 Введите текст приветствия.\n"
        "Шаблоны: {first_name}, {username}, {chat_title}. HTML разрешен."
    )
    await state.set_state(WelcomeStates.waiting_for_welcome)
    await cq.answer()

@router.message(WelcomeStates.waiting_for_welcome)
async def process_welcome_text(message: Message, state: FSMContext):
    data   = await state.get_data(); chat_id = data['chat_id']
    text   = message.text.strip()
    set_welcome_message(chat_id, text)
    await message.answer(f"✅ Приветствие установлено:\n\n{text}")
    await send_log(
        bot, chat_id,
        f"✏️ Приветствие изменено админом {message.from_user.full_name} "
        f"(@{message.from_user.username or '—'}):\n{text}"
    )
    await state.clear()


# 5) Новый участник
@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_user_join(event: ChatMemberUpdated):
    if event.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return
    welcome = get_welcome_message(event.chat.id)
    user    = event.new_chat_member.user
    if welcome:
        await event.answer(
            welcome.format(
                first_name=user.first_name or "",
                username=f"@{user.username}" if user.username else "",
                chat_title=event.chat.title
            ),
            parse_mode="HTML"
        )
    await send_log(
        bot, event.chat.id,
        f"👤 Новый участник: {user.full_name} @{user.username or '—'} (#u{user.id})"
    )


# 6) Установка правил
@router.callback_query(F.data.startswith("setup_rules:"))
async def callback_setup_rules(cq: CallbackQuery, state: FSMContext):
    chat_id = int(cq.data.split(":",1)[1])
    if not await is_admin_in_chat(chat_id, cq.from_user.id):
        return await cq.answer("❌ Только админ может.", show_alert=True)
    await state.update_data(chat_id=chat_id)
    current = get_rules(chat_id) or "(не заданы)"
    await cq.message.answer(f"🔧 Текущие правила:\n{current}\n\nВведите новые правила (HTML).")
    await state.set_state(RulesStates.waiting_for_rules)
    await cq.answer()

@router.message(RulesStates.waiting_for_rules)
async def process_rules_text(message: Message, state: FSMContext):
    data   = await state.get_data(); chat_id = data['chat_id']
    text   = message.text.strip()
    set_rules(chat_id, text)
    await message.answer(f"✅ Правила установлены:\n\n{text}")
    await send_log(
        bot, chat_id,
        f"✏️ Правила изменены админом {message.from_user.full_name} "
        f"(@{message.from_user.username or '—'}):\n{text}"
    )
    await state.clear()


# 7) Кнопка «Логирование» — теперь с вопросом при включении
@router.callback_query(F.data.startswith("logging:"))
async def callback_logging(cq: CallbackQuery, state: FSMContext):
    chat_id   = int(cq.data.split(":",1)[1])
    settings  = get_log_settings(chat_id) or {}
    log_id    = settings.get('log_chat_id')
    enabled   = settings.get('is_logging_enabled', False)

    if not log_id:
        # нет чата — сразу запрашиваем ID
        await cq.message.answer(
            "📥 Введите ID чата для логирования.",
            parse_mode="HTML"
        )
        await state.update_data(chat_id=chat_id)
        await state.set_state(LoggingStates.waiting_for_log_chat_id)
        return await cq.answer()

    if not enabled:
        # включаем: спрашиваем, хотим ли сменить чат
        kb = InlineKeyboardMarkup(row_width=2, inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, сменить", callback_data=f"logging_change:yes:{chat_id}"),
                InlineKeyboardButton(text="Нет, оставить", callback_data=f"logging_change:no:{chat_id}")
            ]
        ])
        await cq.message.answer(
            "Хотите сменить чат для логирования?",
            reply_markup=kb
        )
        return await cq.answer()

    # если уже включено — выключаем сразу
    update_log_status(chat_id, False)
    await cq.answer("🔕 Логирование отключено", show_alert=True)
    await send_log(
        bot, chat_id,
        f"🔕 Логирование отключено админом {cq.from_user.full_name}"
    )
    # обновим меню
    await callback_manage_uc(cq)


# 8) Обработка «Да/Нет» смены чата
@router.callback_query(F.data.startswith("logging_change:"))
async def callback_logging_change(cq: CallbackQuery, state: FSMContext):
    _, ans, chat_id_str = cq.data.split(":")
    chat_id = int(chat_id_str)

    if ans == "yes":
        # переходим в FSM для нового ID
        await cq.message.answer(
            "📥 Введите новый ID чата для логирования.",
            parse_mode="HTML"
        )
        await state.update_data(chat_id=chat_id)
        await state.set_state(LoggingStates.waiting_for_log_chat_id)

    else:
        # оставляем старый ID, просто включаем флаг
        update_log_status(chat_id, True)
        await cq.answer("🔔 Логирование включено", show_alert=True)
        await send_log(
            bot, chat_id,
            f"🔔 Логирование включено админом {cq.from_user.full_name}"
        )
        await callback_manage_uc(cq)


# 9) FSM: сохраняем новый ID или обрабатываем 'off'
@router.message(LoggingStates.waiting_for_log_chat_id)
async def process_log_chat_id(message: Message, state: FSMContext):
    data    = await state.get_data()
    chat_id = data["chat_id"]
    text    = message.text.strip()

    if text.lower() == "off":
        update_log_status(chat_id, False)
        await message.answer("✅ Логирование отключено.")
    else:
        try:
            new_id = int(text)
            await bot.send_message(new_id, "✅ Логирование подключено.")
            set_log_chat(chat_id, new_id)
            update_log_status(chat_id, True)
            ch = await bot.get_chat(new_id)
            title = ch.title or ch.username or str(new_id)
            await message.answer(f"✅ Логирование подключено в чат: {title}")
        except Exception as e:
            return await message.answer(
                f"❌ Не удалось установить лог-чат: {e}"
            )

    await state.clear()
    # обновляем меню
    fake = CallbackQuery(
        id=message.message_id.__str__(),
        from_user=message.from_user,
        chat_instance="",
        message=message,
        data=f"manage_uc:{chat_id}"
    )
    await callback_manage_uc(fake)


# 10) Удаление чата из списка пользователя
@router.callback_query(F.data.startswith("delete_chat:"))
async def callback_delete_chat(cq: CallbackQuery):
    chat_id = int(cq.data.split(":",1)[1])
    remove_user_chat(cq.from_user.id, chat_id)
    await cq.message.edit_text("Чат удалён из вашего списка.")
    await cq.answer("Готово!")
    await send_log(
        bot, chat_id,
        f"🗑️ Чат удалён из списка пользователем {cq.from_user.full_name}"
    )

# Новый обработчик «Назад» — возвращает к списку всех чатов
@router.callback_query(F.data == "back_to_chats")
async def callback_back_to_chats(cq: CallbackQuery):
    user_id = cq.from_user.id
    uc = get_user_chats(user_id)
    if not uc:
        await cq.message.edit_text(
            "У вас ещё нет чатов. Добавьте через команду «установка»",
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