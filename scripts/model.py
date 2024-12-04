from typing import Optional
from pydantic import ConfigDict
from sqlmodel import Field, SQLModel
from enum import Enum


class TicketStatus(str, Enum):
    PURCHASED = "PURCHASED"
    RESERVED = "RESERVED"
    CANCELED = "CANCELED"
    USED = "USED"

    @classmethod
    def from_string(cls, genre_str: str) -> Optional["TicketStatus"]:
        try:
            return cls(genre_str.lower())
        except ValueError:
            return None


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    username: str = Field(index=True)
    password: str = Field()


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    price: float = Field()


class Ticket(SQLModel, table=True):
    model_config: ConfigDict = {"use_enum_values": True}
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    status: TicketStatus = Field()

    def __init__(self, user_id: int, event_id: int, status: TicketStatus):
        self.user_id = user_id
        self.event_id = event_id
        self.status = status

    def __str__(self):
        return f"Ticket {self.id} - STATUS:{self.status} - USER:{self.user_id} - EVENT:{self.event_id}"
