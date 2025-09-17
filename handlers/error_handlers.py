from aiogram import Router, Bot
from aiogram.types import ErrorEvent
from config import ADMIN_CHAT_ID
import traceback
import logging

logger = logging.getLogger(__name__)

error_router = Router(name=__name__)


@error_router.error()
async def error_handler(event: ErrorEvent, bot:Bot):
    """
    Глобальный обработчик всех ошибок в боте
    """
    logger.error(f"Error: {event.exception}", exc_info=True)
    error_message = "🚨 <b>Ошибка в боте:</b>\n\n"
    error_message += f"<b>Тип:</b> {type(event.exception).__name__}\n"
    error_message += f"<b>Описание:</b> {str(event.exception)}\n"
    
    # Информация об обновлении
    if event.update.message:
        msg = event.update.message
        error_message += f"<b>Тип события:</b> message\n"
        error_message += f"<b>Пользователь:</b> {msg.from_user.id}"
        if msg.from_user.username:
            error_message += f" (@{msg.from_user.username})"
        error_message += f"\n<b>Текст сообщения:</b> {msg.text or 'Нет текста'}\n"
    elif event.update.callback_query:
        cb = event.update.callback_query
        error_message += f"<b>Тип события:</b> callback_query\n"
        error_message += f"<b>Пользователь:</b> {cb.from_user.id}"
        if cb.from_user.username:
            error_message += f" (@{cb.from_user.username})"
        error_message += f"\n<b>Callback data:</b> {cb.data}\n"
    
    # Traceback
    tb = traceback.format_exc()
    if len(tb) > 2000:
        tb = tb[:2000] + "\n... (обрезано)"
    error_message += f"\n<code>{tb}</code>"
    
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=error_message,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send error message to admin: {e}")
    return True