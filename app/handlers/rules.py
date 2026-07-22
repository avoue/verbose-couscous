from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..keyboards import MAIN_MENU_BUTTONS

router = Router(name="rules")

RULES_TEXT = (
    "📜 <b>Правила игры</b>\n\n"
    "Игра носит исключительно развлекательный характер. Кредиты — виртуальная валюта, "
    "не имеющая реальной ценности: их нельзя купить, вывести или обменять на что-либо. "
    "Результаты определяются случайно, шансы 50/50. Администрация не несёт ответственности "
    "за возможные эмоциональные последствия.\n\n"
    "Играя, ты подтверждаешь, что тебе исполнилось 18 лет и ты согласен с этими условиями."
)


@router.message(Command("rules"))
async def cmd_rules(message: Message):
    await message.answer(RULES_TEXT)


@router.message(F.text == MAIN_MENU_BUTTONS["rules"])
async def btn_rules(message: Message):
    await message.answer(RULES_TEXT)
