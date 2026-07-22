from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

MAIN_MENU_BUTTONS = {
    "play": "🎲 Играть",
    "balance": "💰 Баланс",
    "bonus": "🎁 Бонус",
    "top": "🏆 Рейтинг",
    "referral": "👥 Рефералы",
    "rules": "📜 Правила",
}

BET_PRESETS = [10, 50, 100, 500]


def main_menu_kb() -> ReplyKeyboardMarkup:
    b = MAIN_MENU_BUTTONS
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=b["play"]), KeyboardButton(text=b["balance"])],
            [KeyboardButton(text=b["bonus"]), KeyboardButton(text=b["top"])],
            [KeyboardButton(text=b["referral"]), KeyboardButton(text=b["rules"])],
        ],
        resize_keyboard=True,
    )


def rules_accept_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Принимаю", callback_data="rules_accept")]]
    )


def bet_amount_kb(balance: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for preset in BET_PRESETS:
        if preset <= balance:
            row.append(InlineKeyboardButton(text=str(preset), callback_data=f"bet_{preset}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    if balance > 0:
        rows.append([InlineKeyboardButton(text=f"Всё ({balance})", callback_data="bet_all")])

    rows.append([InlineKeyboardButton(text="✏️ Своя сумма", callback_data="bet_custom")])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="bet_cancel")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
