from aiogram import Bot, F, Router
from aiogram.types import Message

from ..database import get_session_factory
from ..keyboards import MAIN_MENU_BUTTONS
from ..services import get_user_by_telegram_id

router = Router(name="referral")


@router.message(F.text == MAIN_MENU_BUTTONS["referral"])
async def show_referral(message: Message, bot: Bot):
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введи команду /start")
            return

        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user.ref_code}"

        text = (
            "👥 <b>Реферальная программа</b>\n\n"
            "Приглашай друзей — за каждого зарегистрировавшегося по твоей ссылке ты "
            "получаешь бонусные кредиты (внутриигровые, без возможности вывода).\n\n"
            f"Твоя ссылка:\n{link}\n\n"
            f"Приведено друзей: {user.referral_count}\n"
            f"Получено бонусов: {user.referral_bonus_earned} кредитов"
        )
        await message.answer(text, disable_web_page_preview=True)
