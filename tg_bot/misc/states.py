from aiogram.dispatcher.filters.state import StatesGroup, State


class LoginStates(StatesGroup):
    login = State()
    password = State()
    loggedIn = State()
    edit_note = State()
