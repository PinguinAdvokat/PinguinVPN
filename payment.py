import json
import storage
from aiogram import Bot
from yoomoney import Client
from  config import YOOMONEY_TOKEN


client = Client(token=YOOMONEY_TOKEN)


async def update_clients(bot: Bot):
    bd_history = storage.get_operations_history()
    try:
        history = client.operation_history().operations
    except:
        return
    if len(bd_history) != 0:
        for i in range(len(history)):
            if not (history[i].operation_id, history[i].label) in bd_history:
                js = json.loads(history[i].label)
                storage.remove_promo(js["pr"], js["chat_id"])
                await storage.extend_user(js["chat_id"], int(js["months"]) * 30)
                storage.add_operations_history(history[i].operation_id, history[i].label)
                await bot.send_message(js["chat_id"], f"Тариф успешно продлен на {js["months"]} месяц(ов), приятного пользования !\n(По всем вопросам обращайтесь в поддержку)")
    else:
        for i in range(len(history)):
            storage.add_operations_history(history[i].operation_id, history[i].label)
