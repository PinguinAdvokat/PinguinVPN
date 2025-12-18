import asyncio
import decimal
import storage
import json
import uuid
from pinguins import info1, info2
from aiohttp import ClientSession
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import (Message, CallbackQuery,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from config import VPN_SUBSCRIPTION_ADRESS, YOOMONEY_RECEIVER, YOOMONEY_TOKEN, INFO_CHAT_ID
from guide import PHOTOS_IDS, MESSAGES


ro = Router(name=__name__)
start_message="Используйте команду /menu"
menu_text="Выберите интересующий раздел. Если что-то не работает или у вас есть вопрос обратитесь в поддержку /support"

menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Мой профиль", callback_data="get_vless"), InlineKeyboardButton(text="Тарифы", callback_data="pay")],
                                                      [InlineKeyboardButton(text="Промокод", callback_data="promo"), InlineKeyboardButton(text="Гайд", callback_data="guide")],
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
class Promo(StatesGroup):
    promo_state = State()


async def create_payment(chat_id:int, months:int, price:int, promo:str=""):
    label = {
        "chat_id": chat_id,
        "months": months,
        "pr": promo
    }
    async with ClientSession() as session:
        url = 'https://yoomoney.ru/quickpay/confirm'
        params = {
            'receiver': YOOMONEY_RECEIVER,
            'quickpay-form': 'shop',
            'sum': price,
            'label': str(label)
        }
        async with session.post(url=url, headers={'Authorization': YOOMONEY_TOKEN}, params=params, allow_redirects=False) as response:
            return response.headers.get('Location')


@ro.message(CommandStart())
async def start(message:Message):
    username = message.from_user.username
    if not username:
        username = str(uuid.uuid1())
    user = storage.User(message.chat.id, username, subID=str(uuid.uuid1()), client_id=str(uuid.uuid1()))
    ok = await storage.add_user(user)
    if ok:
        await message.answer(f"вы были успешно зарегистрированы\n{start_message}\nПервый месяц бесплатно!")
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
    await state.set_state(Support.report_text)
    await message.answer("Опишите вашу проблему в одном сообщении", reply_markup=back_keyboard)



@ro.message(Command("get_chat_id"))
async def get_chat_id(message:Message):
  await message.answer(f"{message.chat.id}")


@ro.callback_query(lambda c: c.data == "get_vless")
async def get_vless(callback: CallbackQuery):
    await callback.message.edit_text(f"Скопируйте данный профиль и вставьте в приложение ( нажав на (+) в правом верхнем углу)\n<pre>{VPN_SUBSCRIPTION_ADRESS}/{storage.get_user(callback.message.chat.id).subID}</pre>")
    await callback.message.edit_reply_markup(reply_markup=back_keyboard)


@ro.callback_query(lambda c: c.data == "menu")
async def menu(callback: CallbackQuery, state:FSMContext):
    await state.clear()
    await callback.message.edit_text(menu_text)
    await callback.message.edit_reply_markup(reply_markup=menu_keyboard)


@ro.callback_query(lambda c: c.data[:6] == "remenu")
async def menu_pinguin(callback:CallbackQuery):
    await callback.message.delete()
    print(callback.data[6:])
    await callback.bot.delete_messages(callback.message.chat.id, json.loads(callback.data[6:]))
    await callback.message.answer(menu_text, reply_markup=menu_keyboard)


@ro.callback_query(lambda c: c.data == "pay")
async def pay(callback: CallbackQuery):
    await callback.message.edit_text("выберети на сколько продлить тариф:")
    await callback.message.edit_reply_markup(reply_markup=pay_keyboard)


@ro.callback_query(lambda c: c.data[:6] == "extend")
async def extend(callback: CallbackQuery):
    mounts = callback.data[6:]
    if mounts == "1":
        price = 120
    elif mounts == "2":
        price = 220
    elif mounts == "3":
        price = 310
    else:
        await callback.answer("Возникла ошибка. Попробуйте позже")
        raise Exception("отсутствует callback для продления")
    print("creating payment...")
    url = await create_payment(callback.message.chat.id, int(mounts), price)
    print('done')
    await callback.message.edit_text(f"Продление на {mounts} месяц за {price} рублей.\nСсылка для оплаты:")
    await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=url)],
                                                                                                [InlineKeyboardButton(text="Назад", callback_data="menu")]]))


@ro.callback_query(lambda c: c.data == "pinguins")
async def pinguins(callback:CallbackQuery):
    msg1 = await callback.message.answer(info1)
    await callback.message.delete()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=f"remenu{json.dumps([msg1.message_id])}")]])
    await callback.message.answer(info2, reply_markup=keyboard)


@ro.callback_query(lambda c: c.data == "download")
async def download(callback: CallbackQuery):
    await callback.message.edit_text("Приложение для подключения VPN")
    await callback.message.edit_reply_markup(reply_markup=download_keyboard)


@ro.callback_query(lambda c: c.data == "guide")
async def guide(callback:CallbackQuery):
    await callback.message.delete()
    mess = []
    mess.append(await callback.message.answer(MESSAGES[0]))
    mess.append(await callback.message.answer_photo(photo=PHOTOS_IDS[0]))
    mess.append(await callback.message.answer_photo(photo=PHOTOS_IDS[1]))
    mess.append(await callback.message.answer(MESSAGES[1]))
    for i in range(len(mess)):
        mess[i] = mess[i].message_id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=f"remenu{json.dumps(mess)}")]])
    await callback.message.answer_photo(photo=PHOTOS_IDS[2], reply_markup=keyboard)


@ro.callback_query(lambda c: c.data == "promo")
async def promo(callback:CallbackQuery, state:FSMContext):
    await state.set_state(Promo.promo_state)
    await callback.message.edit_text("Если у вас есть промокод можете написать его")
    await callback.message.edit_reply_markup(reply_markup=back_keyboard)


@ro.message(Promo.promo_state)
async def promo_state(message:Message, state:FSMContext):
    print("promo")
    await state.clear()
    await asyncio.sleep(3)
    promo = storage.use_promo(message.text, message.chat.id)
    if promo:
        if promo["price"] == 0:
            await storage.extend_user(message.chat.id, promo["months"] * 30)
            storage.remove_promo(message.text, message.chat.id)
            await message.answer(f'ваш профиль продлён на {promo["months"]} месяц', reply_markup=back_keyboard)
        else:
            url = create_payment(message.chat.id, promo["months"], promo["price"], promo=message.text)
            await message.answer(f'по промокоду {message.text} можно продлить профиль на {promo["months"]} месяц за {promo["price"]} рублей', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=url)],
                                                                                                                                                                               [InlineKeyboardButton(text="Назад", callback_data="menu")]]))
    else:
        await message.answer("промокод не найден")

@ro.message(Support.report_text)
async def report(message:Message, state:FSMContext):
    await message.bot.send_message(INFO_CHAT_ID, f"Получена жалоба от пользователя {message.from_user.username} chat_id: {message.chat.id}")
    await message.send_copy(INFO_CHAT_ID)
    await state.clear()
    await message.answer("сообщение успешно отправлено поддержке")


@ro.callback_query(lambda c: c.data.split("_")[0] == "que")
async def question(callback:CallbackQuery):
    data = callback.data.split("_")
    storage.answer(data[1], data[2], callback.from_user.username)
    await callback.answer("Спасибо за ответ")
    await callback.message.delete()
