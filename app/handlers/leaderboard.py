from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import desc, select

from ..database import get_session_factory
from ..keyboards import MAIN_MENU_BUTTONS
from ..models import User

router = Router(name="leaderboard")


async def _build_leaderboard_text() -> str:
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(
            select(User)
            .where(User.nickname.is_not(None))
            .order_by(desc(User.total_won))
            .limit(10)
        )
        users = result.scalars().all()

    if not users:
        return "Пока никто не выигрывал. Стань первым! 🎲"

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Топ-10 по выигрышам</b>\n"]
    for i, u in enumerate(users):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{prefix} {u.nickname} — {u.total_won} кредитов (побед: {u.total_wins})")

    return "\n".join(lines)


@router.message(Command("top"))
async def cmd_top(message: Message):
    await message.answer(await _build_leaderboard_text())


@router.message(F.text == MAIN_MENU_BUTTONS["top"])
async def btn_top(message: Message):
    await message.answer(await _build_leaderboard_text())
