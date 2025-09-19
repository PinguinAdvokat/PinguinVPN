import asyncio
import decimal
import storage
import json
import uuid
from pinguins import info1, info2
from yoomoney import Quickpay
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import (Message, CallbackQuery, 
                           InlineKeyboardMarkup, InlineKeyboardButton)
from config import VPN_SUBSCRIPTION_ADRESS, YOOMONEY_RECEIVER, INFO_CHAT_ID


ro = Router(name=__name__)
start_message="Используйте команду /menu"
menu_text="Выберите интересующий раздел"

menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Мой профиль", callback_data="get_vless")],
                                                      [InlineKeyboardButton(text="Тарифы", callback_data="pay")],
                                                      [InlineKeyboardButton(text="Скачать приложение", callback_data="download")],
                                                      [InlineKeyboardButton(text="кто такие пингвины", callback_data="pinguins")]])
back_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="menu")]])
pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Продлить на 1 месяц (120 руб.)", callback_data="extend1")],
                                                     [InlineKeyboardButton(text="Продлить на 2 месяц (220 руб.)", callback_data="extend2")],
                                                     [InlineKeyboardButton(text="Продлить на 3 месяц (330 руб.)", callback_data="extend3")],
                                                     [InlineKeyboardButton(text="Назад", callback_data="menu")]])
download_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="v2RayTun для Android", url="https://play.google.com/store/apps/details?id=com.v2raytun.android")],
                                                          [InlineKeyboardButton(text="v2RayTun для IOS", url="https://apps.apple.com/ru/app/v2raytun/id6476628951")],
                                                          [InlineKeyboardButton(text="Назад", callback_data="menu")]])

class Support(StatesGroup):
    report_text = State()


@ro.message(CommandStart())
async def start(message:Message):
    username = message.from_user.username
    if username == "":
        username = str(uuid.uuid1())
    user = storage.User(message.chat.id, username, subID=str(uuid.uuid1()), client_id=str(uuid.uuid1()))
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


@ro.message(Command("support"))
async def support(message:Message, state:FSMContext):
    await message.answer("Опишите вашу проблему в одном сообщении")
    await state.set_state(Support.report_text)


@ro.message(Command("get_chat_id"))
async def get_chat_id(message:Message):
  await message.answer(f"{message.chat.id}")


@ro.callback_query(lambda c: c.data == "get_vless")
async def get_vless(callback: CallbackQuery):
    await callback.message.edit_text(f"Скопируйте данный профиль и вставьте в приложение ( нажав на (+) в правом верхнем углу)\n<pre>{VPN_SUBSCRIPTION_ADRESS}/{storage.get_user(callback.message.chat.id).subID}</pre>")
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
        sum = 5
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
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=quickpay.redirected_url)],
                                                                                                [InlineKeyboardButton(text="Назад", callback_data="menu")]]))


@ro.callback_query(lambda c: c.data == "pinguins")
async def pinguins(callback:CallbackQuery):
    msg1 = await callback.message.answer(info1)
    await callback.message.delete()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=f"menu{json.dumps([msg1.message_id])}")]])
    await callback.message.answer(info2, reply_markup=keyboard)
    

@ro.callback_query(lambda c: c.data == "download")
async def download(callback: CallbackQuery):
    await callback.message.edit_text("Приложение для подключения VPN")
    await callback.message.edit_reply_markup(reply_markup=download_keyboard)


@ro.callback_query(lambda c: c.data[:4] == "menu")
async def menu_pinguin(callback:CallbackQuery):
    print(callback.data[4:])
    await callback.message.delete()
    await callback.bot.delete_messages(callback.message.chat.id, json.loads(callback.data[4:]))
    await callback.message.answer(menu_text, reply_markup=menu_keyboard)


@ro.message(Support.report_text)
async def report(message:Message, state:FSMContext):
    await message.bot.send_message(INFO_CHAT_ID, f"Получена жалоба от пользователя {message.from_user.username}")
    await message.send_copy(INFO_CHAT_ID)
    await state.clear()
    await message.answer("сообщение успешно отправлено поддержке")