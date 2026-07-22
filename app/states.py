from aiogram.fsm.state import State, StatesGroup


class NicknameStates(StatesGroup):
    waiting_for_nickname = State()


class BetStates(StatesGroup):
    waiting_for_amount = State()
