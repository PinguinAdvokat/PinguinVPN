import storage
import json
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart
from aiogram.types import (Message, CallbackQuery,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from config import ADMIN_CHAT_IDS


admin_r = Router(name=__name__)
class Spam(StatesGroup):
    users = State()
    text = State()
class Create_promo(StatesGroup):
    name = State()
    months = State()
    price = State()
    usage = State()
class Vote(StatesGroup):
    question = State()
    answers = State()


@admin_r.message(Command("users"))
async def users(message: Message):
    if message.chat.id in ADMIN_CHAT_IDS:
        await message.answer(str(storage.sql_get("SELECT * FROM users")))


@admin_r.message(Command("extend_user"))
async def extend_user(message: Message):
    if message.chat.id in ADMIN_CHAT_IDS:
        user = storage.get_user_by_username(message.text.split(" ")[1])
        if user:
            await storage.extend_user(user.chat_id, int(message.text.split(" ")[2]))
            await message.answer("пользователь продлён на месяц")
        else:
            await message.answer("пользователь не найден")


@admin_r.message(Command("spam"))
async def set_spam(message:Message, state:FSMContext):
    if message.chat.id in ADMIN_CHAT_IDS:
        await state.set_state(Spam.text)
        users = storage.sql_get("SELECT chat_id FROM users")
        for i in range(len(users)):
            users[i] = users[i][0]
        await state.set_data({"users": users})
        await message.answer("напишите сообщение для рассылки ВСЕМ пользователям")


@admin_r.message(Command("send"))
async def send(message:Message, state:FSMContext):
    if message.chat.id in ADMIN_CHAT_IDS:
        await message.answer("кому отправить сообщение? (через пробел)")
        await state.set_state(Spam.users)


@admin_r.message(Command("admin"))
async def admin_panel(message:Message):
    if message.chat.id in ADMIN_CHAT_IDS:
        await message.answer("продлить пользователя на n дней месяц /extend_user username n\nпоставить дату окончания на вчера /reset_user username\nсписок всех пользователей /users\nмассовая рассылка /spam\nвыборачная рассылка /send")


@admin_r.message(Command("reset_user"))
async def reset_user(message:Message):
    if message.chat.id in ADMIN_CHAT_IDS:
        if await storage.reset_user(message.text[12:]):
            await message.answer("успешно сброшен")
        else:
            await message.answer("пользователь не найден")


@admin_r.message(Command("get_photo_id"))
async def get_photo_id(message:Message):
    if message.chat.id in ADMIN_CHAT_IDS:
        await message.answer(f"<pre>{message.photo[-1].file_id}</pre>")


@admin_r.message(Command("create_promo"))
async def create_promo(message:Message, state:FSMContext):
    if message.chat.id in ADMIN_CHAT_IDS:
        await state.set_state(Create_promo.name)
        await message.answer("название промокода (уникальное)")


@admin_r.message(Create_promo.name)
async def promo_name(message:Message, state:FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Create_promo.months)
    await message.answer("количество месяцев для продления")


@admin_r.message(Create_promo.months)
async def promo_months(message:Message, state:FSMContext):
    await state.update_data(months=int(message.text))
    await state.set_state(Create_promo.price)
    await message.answer("стоимость для оплаты по промокоду (0 = бесплатно)")


@admin_r.message(Create_promo.price)
async def promo_price(message:Message, state:FSMContext):
    await state.update_data(price=int(message.text))
    await state.set_state(Create_promo.usage)
    await message.answer("количество использований")


@admin_r.message(Create_promo.usage)
async def promo_usage(message:Message, state:FSMContext):
    data = await state.get_data()
    if storage.create_promo(data["name"], data["months"], data["price"], int(message.text)):
        await message.answer("промокод успешно добавлен")
    else:
        await message.answer("такой промокод уже есть")
    await state.clear()


@admin_r.message(Command("delete_promo"))
async def del_promo(message:Message):
    if message.chat.id in ADMIN_CHAT_IDS:
        storage.delete_promo(message.text[14:])
        await message.answer("успешно удалён")


@admin_r.message(Command("get_vote"))
async def get_vote(message:Message):
    if message.chat.id in ADMIN_CHAT_IDS:
        with open("questioners.json", "r") as f:
            data = json.load(f)
        await message.answer(data)


@admin_r.message(Command("vote"))
async def vote(message:Message, state:FSMContext):
    if message.chat.id in ADMIN_CHAT_IDS:
        await message.answer("Вопрос:")
        await state.set_state(Vote.question)


@admin_r.message(Vote.question)
async def vote_question(message:Message, state:FSMContext):
    await state.update_data(question=message.text)
    await message.answer("Варианты ответа через пробел")
    await state.set_state(Vote.answers)


@admin_r.message(Vote.answers)
async def answers(message:Message, state:FSMContext):
    text = await state.get_data()
    answers = message.text.split(" ")
    t = {}
    for i in answers:
        t.update({i: []})
    storage.add_questionary(text["question"], t)


@admin_r.message(Spam.users)
async def users(message:Message, state:FSMContext):
    users = str(message.text).split(' ')
    storage.cursor.execute("SELECT chat_id FROM users WHERE username=%s", users)
    ids = storage.cursor.fetchall()
    if len(ids) == 0:
        await message.answer("пользователи не найдены")
        await state.clear()
        return
    for i in range(len(ids)):
        users[i] = int(ids[i][0])
    await state.set_data({"users": users})
    await message.answer("напишите сообщение для рассылки этим пользователям")
    await state.set_state(Spam.text)


@admin_r.message(Spam.text)
async def spam(message:Message, state:FSMContext):
    users = await state.get_data()
    for i in users["users"]:
        await message.send_copy(int(i))
    await state.clear()
    await message.answer("сообщение успешно отправлено")
