from src.model import Model
from src.utils import tmsnow

from pydantic import Field
from beanie import Document
from typing import Optional


class Property(Model):
    id: int
    name: str
    price: int
    rent: list[int]
    owner_id: Optional[int] = None


class Player(Model):
    player_id: int
    position: int = 0
    balance: int = 1500
    properties: list[Property] = Field(default_factory=list)


class Game(Document):
    max_players: int
    players: list[Player] = Field(default_factory=list)
    board: list[Property] = Field(default_factory=list)

    status: str = Field('waiting')  # waiting, active, finished
    current_index: int = 0  # index of the current player

    started_at: Optional[int] = None
    created_at: int = Field(default_factory=tmsnow)

    def to_dict(self, **kwargs) -> dict:
        return self.model_dump(mode='json', **kwargs)

    class Settings:
        name = 'games'

