import datetime as dt

from aiogram import F, Router
from aiogram.types import Message

from ..config import Config
from ..database import get_session_factory
from ..keyboards import MAIN_MENU_BUTTONS
from ..services import get_user_by_telegram_id

router = Router(name="bonus")

BONUS_PERIOD = dt.timedelta(hours=24)


def _format_remaining(td: dt.timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} ч {minutes} мин"


@router.message(F.text == MAIN_MENU_BUTTONS["bonus"])
async def claim_bonus(message: Message, config: Config):
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введи команду /start")
            return

        now = dt.datetime.now(dt.timezone.utc)

        if user.last_bonus_time is not None:
            last = user.last_bonus_time
            if last.tzinfo is None:
                last = last.replace(tzinfo=dt.timezone.utc)
            elapsed = now - last
            if elapsed < BONUS_PERIOD:
                remaining = BONUS_PERIOD - elapsed
                await message.answer(
                    f"⏳ Бонус уже получен сегодня. Следующий будет доступен через "
                    f"{_format_remaining(remaining)}."
                )
                return

        user.balance += config.daily_bonus_amount
        user.last_bonus_time = now
        await session.commit()

        await message.answer(
            f"🎁 Ты получил ежедневный бонус: +{config.daily_bonus_amount} кредитов!\n"
            f"Текущий баланс: <b>{user.balance}</b> кредитов."
        )
