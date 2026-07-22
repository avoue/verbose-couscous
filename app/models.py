import datetime as dt

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)

    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_bonus_time: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    total_wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_won: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # net credits won across all games

    ref_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    referred_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # telegram_id of the referrer
    referral_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    referral_bonus_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    accepted_rules: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GameHistory(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    bet_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    dice_result: Mapped[int] = mapped_column(Integer, nullable=False)
    win: Mapped[bool] = mapped_column(Boolean, nullable=False)
    payout: Mapped[int] = mapped_column(Integer, nullable=False)  # net balance change, +bet or -bet
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
