import jwt

from config import config

ALGORITHM = 'HS256'


def encode(payload: dict) -> str:
    return jwt.encode(payload, config.jwt_secret, algorithm=ALGORITHM)


def decode(token: str) -> dict:
    return jwt.decode(token, config.jwt_secret, algorithms=[ALGORITHM])


def create_token(user_id: int, purpose: str = 'auth') -> str:
    payload = {'user_id': user_id, 'purpose': purpose}
    return encode(payload)
