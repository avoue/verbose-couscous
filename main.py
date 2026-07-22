import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import load_config
from app.database import create_tables, init_db
from app.handlers import get_main_router

try:
    from dotenv import load_dotenv

    load_dotenv()  # no-op in production if there's no .env file; convenient for local dev
except ImportError:
    pass


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    config = load_config()

    init_db(config.database_url)
    await create_tables()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(get_main_router())

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("STALZONE-Fun bot starting polling...")
    await dp.start_polling(bot, config=config)


if __name__ == "__main__":
    asyncio.run(main())
