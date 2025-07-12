from src.model import Model
from pydantic import ConfigDict
from typing import Generic, TypeVar

__all__ = ('Paginated',)

T = TypeVar('T')


class Paginated(Model, Generic[T]):
    page: int
    size: int
    total: int
    pages: int
    items: list[T]

    model_config = ConfigDict(extra='ignore')
