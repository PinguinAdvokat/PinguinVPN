import storage
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (Message, CallbackQuery, 
                           InlineKeyboardMarkup, InlineKeyboardButton)
from config import ADMIN_CHAT_ID


admin_r = Router(name=__name__)


@admin_r.message(Command("users"))
async def users(message: Message):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer(str(storage.sql_get("SELECT * FROM users")))


@admin_r.message(Command("extend_user"))
async def extend_user(message: Message):
    if message.chat.id == ADMIN_CHAT_ID:
        user = storage.get_user_by_username(message.from_user.username)
        await storage.extend_user(user.chat_id, 1)
        await message.answer("пользователь продлён на месяц")