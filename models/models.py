from .base_models import Base, TablenameMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BIGINT, VARCHAR, ForeignKey, INTEGER, TEXT, BOOLEAN
from dataclasses import dataclass
from sqlalchemy.sql import expression

@dataclass
class User(Base, TablenameMixin):
    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    username: Mapped[str] = mapped_column(VARCHAR(64), unique=True)
    password: Mapped[str] = mapped_column(TEXT)
    telegram_id: Mapped[int] = mapped_column(BIGINT, unique=True, nullable=True)
    email_verified: Mapped[bool] = mapped_column(BOOLEAN)


@dataclass
class Note(Base, TablenameMixin):
    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    title: Mapped[str] = mapped_column(VARCHAR(64), nullable=True)
    content: Mapped[str] = mapped_column(TEXT)
    mark_as_done: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, server_default=expression.false())

    author_id: Mapped[int] = mapped_column(INTEGER, ForeignKey(User.id))
    author: Mapped[User] = relationship()