from src.model import Model
from src.utils import tmsnow

from beanie import Document
from typing import Optional

from pydantic import Field, \
    EmailStr, HttpUrl, ConfigDict


class Stats(Model):
    win: int = 0
    loss: int = 0
    total: int = 0


class User(Document):
    id: int
    name: str
    email: EmailStr
    avatar: Optional[HttpUrl] = None
    password: str = Field(exclude=True)

    stats: Stats = Field(
        ..., default_factory=Stats
    )

    is_admin: bool = False
    is_active: bool = True

    last_login: Optional[int] = None
    created_at: Optional[int] = Field(
        ..., default_factory=tmsnow
    )

    model_config = ConfigDict(populate_by_name=True)

    def to_dict(self, **kwargs) -> dict:
        return self.model_dump(mode='json', **kwargs)

    def set_last_login(self) -> None:
        self.last_login = tmsnow()

    class Settings:
        name = 'users'
