import json
import storage
from aiohttp import ClientSession, web
from aiohttp.client_exceptions import ClientConnectionError
from aiogram import Bot
from config import YOOMONEY_TOKEN


async def update_clients(bot: Bot):
    bd_history = storage.get_operations_history()
    try:
        print('getting pay history...')
        history = await get_yoomoney_history(YOOMONEY_TOKEN)
        print('done')
    except Exception as e:
        print('error get history: ', e)
        return
    if len(bd_history) != 0:
        for i in range(len(history)):
            try:
                if (not (history[i]['operation_id'], history[i]['label']) in bd_history) and history[i]['label']:
                    js = json.loads(str(history[i]['label']).replace("'", '"'))
                    storage.remove_promo(js["pr"], js["chat_id"])
                    await storage.extend_user(js["chat_id"], int(js["months"]) * 30)
                    storage.add_operations_history(history[i]['operation_id'], history[i]['label'])
                    await bot.send_message(js["chat_id"], f'Тариф успешно продлен на {js["months"]} месяц(ов), приятного пользования !\n(По всем вопросам обращайтесь в поддержку)')
            except KeyError:
                pass
    else:
        for i in range(len(history)):
            storage.add_operations_history(history[i]['operation_id'], history[i]['label'])


async def get_yoomoney_history(token):
    async with ClientSession() as session:
        url = "https://yoomoney.ru/api/operation-history"
        async with session.post(url=url, headers={'Authorization': f'Bearer {token}'}, ) as response:
            if response.status == 200:
                js = await response.json()
                return js['operations']
            print('status: ', response.status)
            print('json: ', await response.json())
            print('text: ', await response.text())
            raise ClientConnectionError()