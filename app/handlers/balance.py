from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..database import get_session_factory
from ..keyboards import MAIN_MENU_BUTTONS
from ..services import get_user_by_telegram_id

router = Router(name="balance")


async def _show_balance(message: Message):
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введи команду /start")
            return
        await message.answer(f"💰 Твой баланс: <b>{user.balance}</b> кредитов.")


@router.message(F.text == MAIN_MENU_BUTTONS["balance"])
async def btn_balance(message: Message):
    await _show_balance(message)


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    await _show_balance(message)
