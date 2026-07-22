from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session_factory
from ..keyboards import MAIN_MENU_BUTTONS, bet_amount_kb, rules_accept_kb
from ..models import GameHistory, User
from ..services import get_user_by_telegram_id
from ..states import BetStates
from ..utils import roll_dice
from .rules import RULES_TEXT

router = Router(name="dice")


@router.message(F.text == MAIN_MENU_BUTTONS["play"])
async def start_play(message: Message, state: FSMContext):
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введи команду /start")
            return

        if not user.accepted_rules:
            await message.answer(RULES_TEXT, reply_markup=rules_accept_kb())
            return

        if user.balance <= 0:
            await message.answer(
                "У тебя пока нет кредитов 😔 Забери «🎁 Бонус», чтобы начать играть!"
            )
            return

        await message.answer(
            f"💰 Баланс: {user.balance} кредитов.\nВыбери сумму ставки:",
            reply_markup=bet_amount_kb(user.balance),
        )


@router.callback_query(F.data == "rules_accept")
async def accept_rules(callback: CallbackQuery):
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if user:
            user.accepted_rules = True
            await session.commit()

    await callback.message.edit_text("Спасибо! Соглашение принято ✅")
    await callback.answer()
    await callback.message.answer("Нажми «🎲 Играть», чтобы сделать ставку.")


@router.callback_query(F.data == "bet_cancel")
async def cancel_bet(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Ставка отменена.")
    await callback.answer()


@router.callback_query(F.data == "bet_custom")
async def ask_custom_bet(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи сумму ставки числом:")
    await state.set_state(BetStates.waiting_for_amount)
    await callback.answer()


@router.callback_query(F.data.startswith("bet_"))
async def process_preset_bet(callback: CallbackQuery):
    payload = callback.data.split("_", 1)[1]
    # "cancel" and "custom" are handled by the dedicated handlers above, which
    # (being registered first) intercept those callback_data values before
    # this handler ever runs. This guard is just defensive.
    if payload in ("cancel", "custom"):
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.answer("Сначала введи /start", show_alert=True)
            return

        bet = user.balance if payload == "all" else int(payload)
        await _resolve_bet(session, user, bet, callback.message)

    await callback.answer()


@router.message(BetStates.waiting_for_amount)
async def process_custom_bet_amount(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Введи целое положительное число.")
        return

    bet = int(text)
    if bet <= 0:
        await message.answer("Ставка должна быть больше нуля.")
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введи команду /start")
            await state.clear()
            return

        if bet > user.balance:
            await message.answer(
                f"У тебя всего {user.balance} кредитов. Введи сумму меньше или равную балансу."
            )
            return

        await state.clear()
        await _resolve_bet(session, user, bet, message)


async def _resolve_bet(session: AsyncSession, user: User, bet: int, reply_target) -> None:
    if bet <= 0 or bet > user.balance:
        await reply_target.answer("Некорректная сумма ставки.")
        return

    result = roll_dice()
    win = result >= 4
    payout = bet if win else -bet  # net balance change

    user.balance += payout
    if win:
        user.total_wins += 1
        user.total_won += bet
    else:
        user.total_losses += 1

    session.add(
        GameHistory(
            user_id=user.id,
            bet_amount=bet,
            dice_result=result,
            win=win,
            payout=payout,
        )
    )
    await session.commit()

    nickname = user.nickname or "Игрок"
    if win:
        text = (
            f"🎲 Выпало: <b>{result}</b>\n\n"
            f"{nickname} побеждает в игре 🎲 на {bet} кредитов!\n"
            f"Выигрыш: {bet * 2} кредитов.\n\n"
            f"💰 Баланс: {user.balance} кредитов."
        )
    else:
        text = (
            f"🎲 Выпало: <b>{result}</b>\n\n"
            f"{nickname} проигрывает {bet} кредитов в игре 🎲.\n\n"
            f"💰 Баланс: {user.balance} кредитов."
        )

    await reply_target.answer(text)
