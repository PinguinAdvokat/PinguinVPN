import asyncio
import decimal
import storage
import json
import uuid
from yoomoney import Quickpay
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (Message, CallbackQuery, 
                           InlineKeyboardMarkup, InlineKeyboardButton)
from config import VPN_SUBSCRIPTION_ADRESS, YOOMONEY_RECEIVER


ro = Router(name=__name__)
start_message="start message. Use /menu"
menu_text="it,s menu text"

menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="мой профиль vless", callback_data="get_vless")],
                                                      [InlineKeyboardButton(text="продлить", callback_data="pay")]])
back_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="menu")]])
pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Продлить на 1 месяц (120 руб.)", callback_data="extend1")],
                                                     [InlineKeyboardButton(text="Продлить на 2 месяц (220 руб.)", callback_data="extend2")],
                                                     [InlineKeyboardButton(text="Продлить на 3 месяц (330 руб.)", callback_data="extend3")]])


@ro.message(CommandStart())
async def start(message:Message):
    username = message.from_user.username
    if username == "":
        username = str(uuid.uuid1())
    user = storage.User(message.chat.id, username)
    ok = await storage.add_user(user)
    if ok:
        await message.answer(f"вы были успешно зарегистрированы\n{start_message}")
    else:
        await message.answer(start_message)


@ro.message(Command("menu"))
async def menu(message:Message):
    if storage.get_user(message.chat.id):
        await message.answer(f"{menu_text}", reply_markup=menu_keyboard)
    else:
        await message.answer("используйте команду /start")


@ro.callback_query(lambda c: c.data == "get_vless")
async def get_vless(callback: CallbackQuery):
    await callback.message.edit_text(f"ваша ссылка на vless (скопируйте её и вставте в hiddify)\n<pre>{VPN_SUBSCRIPTION_ADRESS}/{storage.get_user(callback.message.chat.id).subID}</pre>")
    await callback.message.edit_reply_markup(reply_markup=back_keyboard)
    

@ro.callback_query(lambda c: c.data == "menu")
async def menu(callback: CallbackQuery):
     await callback.message.edit_text(menu_text)
     await callback.message.edit_reply_markup(reply_markup=menu_keyboard)
     

@ro.callback_query(lambda c: c.data == "pay")
async def pay(callback: CallbackQuery):
    await callback.message.edit_text("выберети на сколько продлить тариф:")
    await callback.message.edit_reply_markup(reply_markup=pay_keyboard)


@ro.callback_query(lambda c: c.data[:6] == "extend")
async def extend(callback: CallbackQuery):
    mounts = callback.data[6:]
    if mounts == "1":
        sum = 10
    elif mounts == "2":
        sum = 220
    elif mounts == "3":
        sum = 330
    else:
        await callback.answer("Возникла ошибка. Попробуйте позже")
        raise Exception("отсутствует callback для продления")
    label = {
        "chat_id": callback.message.chat.id,
        "months": int(mounts)
    }
    quickpay = Quickpay(
        receiver=YOOMONEY_RECEIVER,
        quickpay_form="shop",
        targets="Pinguin VPN",
        paymentType="SB",
        sum=sum,
        label=json.dumps(label)
    )
    await callback.message.edit_text(f"Продление на {mounts} месяц за {sum} рублей.\nСсылка для оплаты:")
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=quickpay.redirected_url)]]))