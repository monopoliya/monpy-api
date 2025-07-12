from .models import User
from src.model import Model


class UserPublic(User):
    pass


class AuthResponse(Model):
    token: str
    user: UserPublic
