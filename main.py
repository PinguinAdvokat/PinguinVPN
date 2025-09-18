import logging
import sys
import asyncio
import payment

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from handlers.main_handlers import ro
from handlers.error_handlers import error_router
from handlers.admin_handlers import admin_r


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def payment_loop():
    while True:
        print("update")
        await payment.update_clients(bot)
        await asyncio.sleep(30)


async def main() -> None:
    dp = Dispatcher()
    dp.include_router(ro)
    dp.include_router(error_router)
    dp.include_router(admin_r)
    await asyncio.gather(dp.start_polling(bot), payment_loop())
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    asyncio.run(main())