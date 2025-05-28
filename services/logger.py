from aiogram import Bot
from typing import Optional
import logging

from db import get_log_settings


async def send_log(
        bot: Bot,
        chat_id: int,
        message_text: str,
        parse_mode: Optional[str] = None
) -> None:
    """
    Шлёт в канал логов сообщение message_text,
    если для chat_id включено логирование и задан log_chat_id.
    """
    settings = get_log_settings(chat_id)
    if not settings:
        return

    log_chat_id = settings.get("log_chat_id")
    enabled = settings.get("is_logging_enabled", False)
    if not (enabled and log_chat_id):
        return

    try:
        await bot.send_message(
            chat_id=log_chat_id,
            text=message_text,
            parse_mode=parse_mode
        )
    except Exception as e:
        logging.warning(f"[logger] failed to send log to {log_chat_id}: {e}")
