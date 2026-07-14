import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import create_pool, create_tables
from handlers import router
from aiogram import BaseMiddleware
from handlers import DbSessionMiddleware



async def main():
    logging.basicConfig(level=logging.INFO)
    pool = await create_pool()
    await create_tables(pool)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    dp.message.middleware(DbSessionMiddleware(pool))
    dp.callback_query.middleware(DbSessionMiddleware(pool))


    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())