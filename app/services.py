from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .utils import generate_ref_code


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_user_by_ref_code(session: AsyncSession, ref_code: str) -> User | None:
    result = await session.execute(select(User).where(User.ref_code == ref_code))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    referral_bonus_amount: int,
    ref_payload: str | None = None,
) -> User:
    """Create a new user, crediting the referrer (if any valid ref_payload is given)
    with a one-time bonus for the new registration."""

    # Generate a unique referral code for the new user.
    while True:
        code = generate_ref_code()
        if await get_user_by_ref_code(session, code) is None:
            break

    user = User(
        telegram_id=telegram_id,
        nickname=None,
        balance=0,
        ref_code=code,
        referred_by=None,
    )
    session.add(user)
    await session.flush()  # assign user.id without committing yet

    if ref_payload:
        referrer = await get_user_by_ref_code(session, ref_payload)
        if referrer is not None and referrer.telegram_id != telegram_id:
            user.referred_by = referrer.telegram_id
            referrer.balance += referral_bonus_amount
            referrer.referral_count += 1
            referrer.referral_bonus_earned += referral_bonus_amount

    await session.commit()
    await session.refresh(user)
    return user
