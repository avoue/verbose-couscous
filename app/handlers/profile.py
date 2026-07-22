from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..database import get_session_factory
from ..services import get_user_by_telegram_id

router = Router(name="profile")


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введи команду /start")
            return

        text = (
            "👤 <b>Профиль</b>\n\n"
            f"Никнейм: {user.nickname}\n"
            f"Баланс: {user.balance} кредитов\n"
            f"Побед: {user.total_wins} | Поражений: {user.total_losses}\n"
            f"Всего выиграно: {user.total_won} кредитов\n"
            f"Рефералов приведено: {user.referral_count}\n"
            f"Бонус за рефералов: {user.referral_bonus_earned} кредитов"
        )
        await message.answer(text)
