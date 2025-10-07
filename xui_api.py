import aiohttp
import datetime
import uuid
from config import VPN_API_URL, VPN_API_LOGIN, VPN_API_PASSWORD, VPN_INBOUND_ID

class User():
    def __init__(self, chat_id:int, username:str, subID:str=str(uuid.uuid1()), client_id:str=str(uuid.uuid1()), expire:int=None):
        if not expire:
            date = datetime.datetime.now().timestamp() - 86400
            self.expire = int(date)
        else:
            self.expire = expire
        self.chat_id = chat_id
        self.username = username
        self.subID = subID
        self.client_id = client_id


class Xui_client():
    def __init__(self):
        self._cookies = None

    async def login(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{VPN_API_URL}/login", json={"username": VPN_API_LOGIN, "password": VPN_API_PASSWORD}, ssl=False) as response:
                if response.status == 200:
                    self._cookies = response.cookies.copy()
                    print("logged in 3x-ui")
                else:
                    print("error while logging in 3x-ui:", await response.text)


    async def add_vless_user(self, user:User):
        if not self._cookies:
            await self.login()
        client = f"\"comment\":\"From Pinguin Bot\",\"id\":\"{user.client_id}\",\"alterId\":0,\"email\":\"{user.username}\",\"limitIp\":1,\"totalGB\":0,\"expiryTime\":{user.expire}000,\"flow\": \"xtls-rprx-vision\",\"enable\":true,\"tgId\":\"\",\"subId\":\"{user.subID}\""
        payload = {
            "id": VPN_INBOUND_ID,
            "settings": "{\"clients\":[{"+client+"}]}"
        }
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            async with session.post(f"{VPN_API_URL}/panel/api/inbounds/addClient", data=payload, ssl=False) as response:
                print(f"запрос на добавление пользователя {user.username}: {await response.text()}")
                js = await response.json()
                if response.status == 200 and js["success"]:
                    return True
                raise ConnectionError(f"не удалось добавить пользователя ({response.status}): {await response.text()}")

    async def update_vless_user(self, user:User):
        if not self._cookies:
            await self.login()
        client = f"\"comment\":\"From Pinguin Bot\",\"id\":\"{user.client_id}\",\"alterId\":0,\"email\":\"{user.username}\",\"limitIp\":0,\"totalGB\":0,\"expiryTime\":{user.expire}000,\"flow\": \"xtls-rprx-vision\",\"enable\":true,\"tgId\":\"\",\"subId\":\"{user.subID}\""
        payload = {
            "id": VPN_INBOUND_ID,
            "settings": "{\"clients\":[{"+client+"}]}"
        }
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            async with session.post(f"{VPN_API_URL}/panel/api/inbounds/updateClient/{user.client_id}", data=payload, ssl=False) as response:
                print(f"запрос на обновление пользователя {user.username}: {await response.text()}")
                js = await response.json()
                if response.status == 200 and js["success"]:
                    return True
                raise ConnectionError(f"не удалось обновить пользователя ({response.status}): {await response.text()}")

client = Xui_client()
