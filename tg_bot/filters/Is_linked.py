from aiogram.dispatcher.filters import BoundFilter
from aiogram import types

from sqlalchemy.orm import Session
from sqlalchemy import select

from models.models import User
from tg_bot.services.db import engine


class IsLinkedFilter(BoundFilter):
    key = "is_linked"
    def __init__(self, is_linked: bool):
        self.is_linked = is_linked

    async def check(self, message: types.Message):
        with Session(engine) as session:
            link = session.execute(select(User).where(User.telegram_id == message.from_id)).scalar()
        return (link is not None) == self.is_linked