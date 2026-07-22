from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..config import Config
from ..database import get_session_factory
from ..keyboards import main_menu_kb
from ..services import create_user, get_user_by_telegram_id
from ..states import NicknameStates

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, config: Config, command: CommandObject):
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        is_new = user is None
        if is_new:
            ref_payload = command.args.strip() if command.args else None
            user = await create_user(
                session,
                telegram_id=message.from_user.id,
                referral_bonus_amount=config.referral_bonus_amount,
                ref_payload=ref_payload,
            )

    if not user.nickname:
        await message.answer(
            "Добро пожаловать в <b>STALZONE-Fun</b>! 🎮\n\n"
            "Это развлекательный бот с виртуальными кредитами — они не имеют реальной "
            "ценности, их нельзя купить, вывести или передать другим игрокам.\n\n"
            "Для начала — как тебя называть в статистике? Введи свой игровой никнейм STALZONE:"
        )
        await state.set_state(NicknameStates.waiting_for_nickname)
        return

    await message.answer(
        f"С возвращением, {user.nickname}! 👋\nВыбери действие в меню ниже:",
        reply_markup=main_menu_kb(),
    )


@router.message(NicknameStates.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    nickname = (message.text or "").strip()
    if not (2 <= len(nickname) <= 32):
        await message.answer("Никнейм должен быть от 2 до 32 символов. Попробуй ещё раз:")
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if user is None:
            await message.answer("Что-то пошло не так, попробуй ещё раз команду /start")
            await state.clear()
            return
        user.nickname = nickname
        await session.commit()

    await state.clear()
    await message.answer(
        f"Отлично, {nickname}! Твой профиль создан.\n\nВыбери действие в меню ниже:",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("setnick"))
async def cmd_setnick(message: Message, state: FSMContext):
    await message.answer("Введи новый игровой никнейм STALZONE:")
    await state.set_state(NicknameStates.waiting_for_nickname)
