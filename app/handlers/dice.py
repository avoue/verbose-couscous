import asyncio

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, MessageEntity
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session_factory
from ..keyboards import MAIN_MENU_BUTTONS, bet_amount_kb, rules_accept_kb
from ..models import GameHistory, User
from ..services import get_user_by_telegram_id
from ..states import BetStates
from .rules import RULES_TEXT

router = Router(name="dice")

# Custom emoji IDs supplied for the redesigned result messages, mapped to
# their real fallback glyphs (confirmed from Telegram's own entities when
# these emoji are sent as plain text — see conversation history).
EMOJI_COIN = ("5409048419211682843", "💵")        # money / credits icon
EMOJI_CROSS = ("5449503162849318231", "❌")        # cross mark
EMOJI_ARROW_UP = ("5449683594425410231", "🔼")     # up-pointing triangle (used as separator)
EMOJI_ARROW_DOWN = ("5447183459602669338", "🔽")   # down-pointing triangle

# How long Telegram's native dice animation takes to fully play out.
DICE_ANIMATION_SECONDS = 4.0


def _utf16_len(text: str) -> int:
    """Telegram entity offsets/lengths are counted in UTF-16 code units, NOT
    Python's code-point-based len(). Characters outside the Basic Multilingual
    Plane (most emoji, including 🎲 and the custom-emoji fallback glyphs below)
    are encoded as UTF-16 surrogate pairs (2 units), so len() alone undercounts
    them and silently misaligns every entity that follows."""
    return len(text.encode("utf-16-le")) // 2


def _build_result_message(nickname: str, bet: int, win: bool, balance: int) -> tuple[str, list[MessageEntity]]:
    """Build the win/loss announcement text with custom emoji entities mixed in."""
    entities: list[MessageEntity] = []
    parts: list[str] = []
    cursor = 0

    def add_text(t: str) -> None:
        nonlocal cursor
        parts.append(t)
        cursor += _utf16_len(t)

    def add_emoji(emoji: tuple[str, str]) -> None:
        nonlocal cursor
        custom_emoji_id, placeholder = emoji
        parts.append(placeholder)
        entities.append(
            MessageEntity(
                type="custom_emoji",
                offset=cursor,
                length=_utf16_len(placeholder),
                custom_emoji_id=custom_emoji_id,
            )
        )
        cursor += _utf16_len(placeholder)

    if win:
        add_text(f'"{nickname}" побеждает в игре 🎲 на {bet} ')
        add_emoji(EMOJI_COIN)
        add_text(" ")
        add_emoji(EMOJI_CROSS)
        add_text(f" {bet} ")
        add_emoji(EMOJI_ARROW_UP)
        add_text(f"\nВыигрыш {bet * 2} ")
        add_emoji(EMOJI_COIN)
        add_text(f"\n\n💰 Баланс: {balance} кредитов.")
    else:
        add_text(f'"{nickname}" проигрывает {bet} ')
        add_emoji(EMOJI_COIN)
        add_text(" в игре 🎲 ")
        add_emoji(EMOJI_ARROW_DOWN)
        add_text(" ")
        add_emoji(EMOJI_ARROW_UP)
        add_text(f"\nПроигрыш {bet} ")
        add_emoji(EMOJI_COIN)
        add_text(f"\n\n💰 Баланс: {balance} кредитов.")

    return "".join(parts), entities



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
async def process_preset_bet(callback: CallbackQuery, bot: Bot):
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
        await callback.answer()
        await _resolve_bet(session, user, bet, callback.message, bot)


@router.message(BetStates.waiting_for_amount)
async def process_custom_bet_amount(message: Message, state: FSMContext, bot: Bot):
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
        await _resolve_bet(session, user, bet, message, bot)


async def _resolve_bet(session: AsyncSession, user: User, bet: int, reply_target, bot: Bot) -> None:
    if bet <= 0 or bet > user.balance:
        await reply_target.answer("Некорректная сумма ставки.")
        return

    # Throw the actual animated Telegram dice — this IS the game, not a decoration.
    # message.dice.value is Telegram's own server-side roll (1-6), so the visible
    # animation always matches the real outcome.
    dice_message = await bot.send_dice(chat_id=reply_target.chat.id, emoji="🎲")
    result = dice_message.dice.value

    # Let the animation fully play out in the user's client before revealing the outcome.
    await asyncio.sleep(DICE_ANIMATION_SECONDS)

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
    text, entities = _build_result_message(nickname, bet, win, user.balance)
    # parse_mode=None is required here: the bot has a global default parse_mode
    # (HTML). If parse_mode is set on a call, Telegram ignores the `entities`
    # parameter entirely, so the custom emoji would silently fail to render.
    await bot.send_message(
        chat_id=reply_target.chat.id,
        text=text,
        entities=entities,
        parse_mode=None,
    )
