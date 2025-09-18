import json
import storage
from aiogram import Bot
from yoomoney import Client
from  config import YOOMONEY_TOKEN


client = Client(token=YOOMONEY_TOKEN)


async def update_clients(bot: Bot):
    bd_history = storage.get_operations_history()
    history = client.operation_history().operations
    if len(bd_history) != 0:
        for i in range(len(history)):
            if not (history[i].operation_id, history[i].label) in bd_history:
                js = json.loads(history[i].label)
                await storage.extend_user(js["chat_id"], js["months"])
                storage.add_operations_history(history[i].operation_id, history[i].label)
                await bot.send_message(js["chat_id"], f"ваш профиль продлён на {js["months"]} месяц.\nКоллеги, не ходите на сайты с порнографией. Весь ваш трафик под контролем. Попадёте на запрещённый ресурс — будут проблемы. Не усложняйте себе жизнь.")
    else:
        for i in range(len(history)):
            storage.add_operations_history(history[i].operation_id, history[i].label)