import asyncio
from aiohttp import ClientSession

async def create_payment(chat_id:int, months:int, price:int, promo:str=""):
    label = {
        "chat_id": chat_id,
        "months": months,
        "pr": promo
    }
    async with ClientSession() as session:
        url = 'https://yoomoney.ru/quickpay/confirm'
        params = {
            'receiver': "4100119008899323",
            'quickpay-form': 'shop',
            'sum': price,
            'label': str(label)
        }
        headers = {'User-Agent': 'Mozilla/5.0', 'connection': 'keep-alive', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br'}
        async with session.post(url=url, data=params, headers=headers, allow_redirects=False, ssl=False) as response:
            return response.headers.get('Location')
        
        
def main():
    url = asyncio.run(create_payment(123456789, 3, 1000, "PROMO2024"))
    print(f"Payment URL: {url}")

if __name__ == "__main__":
    main()