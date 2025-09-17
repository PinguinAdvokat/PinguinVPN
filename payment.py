import json
import storage
from yoomoney import Client
from  config import YOOMONEY_TOKEN


client = Client(token=YOOMONEY_TOKEN)


async def update_clients():
    bd_history = storage.get_operations_history()
    history = client.operation_history().operations
    if len(bd_history) != 0:
        for i in range(len(history)):
            if not (history[i].operation_id, history[i].label) in bd_history:
                js = json.loads(history[i].label)
                await storage.extend_user(js["chat_id"], js["months"])
                storage.add_operations_history(history[i].operation_id, history[i].label)
    else:
        for i in range(len(history)):
            storage.add_operations_history(history[i].operation_id, history[i].label)