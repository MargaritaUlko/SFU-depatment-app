from sqlalchemy import Column, String, Integer
from app.db.base import Base, TimestampMixin


class Stream(Base, TimestampMixin):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    speciality = Column(String(255), nullable=False)

    def __str__(self) -> str:
        return self.name
