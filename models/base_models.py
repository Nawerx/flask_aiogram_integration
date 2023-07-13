from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr

class Base(DeclarativeBase):
    pass

class TablenameMixin:
    @declared_attr.directive
    def __tablename__(cls):
        return cls.__name__.lower() + "s"


