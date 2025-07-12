from .models import User
from .forms import UserCreate, UserLogin

from config import config, ALLOWED_DOMAINS
from .public import UserPublic, AuthResponse

import jwt
import hashlib

from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix='/users', tags=['users'])


def _create_token(user_id: int) -> str:
    return jwt.encode({'id': user_id}, config.jwt_secret, algorithm='HS256')


@router.post(
    path='/register',
    response_model=AuthResponse
)
async def register(user: UserCreate):
    domain: str = user.email.split('@')[-1].lower()
    if domain not in ALLOWED_DOMAINS:
        raise HTTPException(400, 'Email domain not allowed')

    existing = await User.find_one(User.email == user.email)
    if existing:
        raise HTTPException(400, 'User already exists')

    last = await User.find().sort('-id').limit(1).to_list(1)
    next_id = last[0].id + 1 if last else 0

    hashed = hashlib.md5(user.password.encode()).hexdigest()
    new_user = User(id=next_id, name=user.name, email=user.email, password=hashed)  # noqa: E501

    await new_user.insert()
    token = _create_token(new_user.id)
    return {'token': token, 'user': new_user}


@router.post(
    path='/login',
    response_model=AuthResponse
)
async def login(credentials: UserLogin):
    user = await User.find_one(User.email == credentials.email)
    if not user:
        raise HTTPException(401, 'Invalid credentials')

    hashed = hashlib.md5(credentials.password.encode()).hexdigest()
    if hashed != user.password:
        raise HTTPException(401, 'Invalid credentials')

    user.set_last_login()
    await user.save()

    token = _create_token(user.id)
    return {'token': token, 'user': user}


@router.get(
    path='/me',
    response_model=UserPublic
)
async def get_me(x_user_id: int = Header(..., alias='x-user-id')):
    user = await User.find_one(User.id == x_user_id)
    if not user:
        raise HTTPException(404, 'User not found')
    return user
