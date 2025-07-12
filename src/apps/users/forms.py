from src.model import Model
from pydantic import EmailStr


class UserCreate(Model):
    name: str
    email: EmailStr
    password: str


class UserLogin(Model):
    email: EmailStr
    password: str
