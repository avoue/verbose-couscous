from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from ..config import Config
from ..database import get_session_factory
from ..services import get_user_by_telegram_id

router = Router(name="admin")


def _is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admin_ids


@router.message(Command("reset_balance"))
async def cmd_reset_balance(message: Message, command: CommandObject, config: Config):
    """Debug-only: zero out a user's balance. Not part of the regular top-up flow —
    credits are only ever earned via the daily bonus or referrals."""
    if not _is_admin(message.from_user.id, config):
        return

    if not command.args:
        await message.answer("Использование: /reset_balance <telegram_id>")
        return

    try:
        target_id = int(command.args.strip().split()[0])
    except ValueError:
        await message.answer("telegram_id должен быть числом.")
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, target_id)
        if not user:
            await message.answer("Пользователь не найден.")
            return
        user.balance = 0
        await session.commit()

    await message.answer(f"Баланс пользователя {target_id} сброшен до 0.")


@router.message(Command("add_credits"))
async def cmd_add_credits(message: Message, command: CommandObject, config: Config):
    """Debug-only: manually add credits for testing. Not intended for regular
    operational use — the bot has no purchase/deposit flow."""
    if not _is_admin(message.from_user.id, config):
        return

    if not command.args:
        await message.answer("Использование: /add_credits <telegram_id> <amount>")
        return

    parts = command.args.strip().split()
    if len(parts) != 2:
        await message.answer("Использование: /add_credits <telegram_id> <amount>")
        return

    try:
        target_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        await message.answer("telegram_id и amount должны быть числами.")
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, target_id)
        if not user:
            await message.answer("Пользователь не найден.")
            return
        user.balance += amount
        await session.commit()
        new_balance = user.balance

    await message.answer(f"Добавлено {amount} кредитов пользователю {target_id}. Новый баланс: {new_balance}.")
