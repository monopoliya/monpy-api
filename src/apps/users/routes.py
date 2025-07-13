from .models import User
from .forms import UserCreate, UserLogin

from config import ALLOWED_DOMAINS
from .public import UserPublic, AuthResponse

from src.jwt import create_token, decode
from src.email import email_exists, send_verification_email

import jwt
import hashlib

from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix='/users', tags=['users'])


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

    if await email_exists(user.email) is False:
        raise HTTPException(400, 'Email does not exist')

    last = await User.find().sort('-id').limit(1).to_list(1)
    next_id = last[0].id + 1 if last else 0

    # hash the password for security
    hashed = hashlib.md5(user.password.encode()).hexdigest()

    new_user = User(
        id=next_id,
        name=user.name,
        email=user.email,
        password=hashed
    )
    # adding new user to db
    await new_user.insert()

    verify_token = create_token(new_user.id, 'verify')
    # Here you would send the verification email with the token
    await send_verification_email(new_user.email, verify_token)

    token = create_token(new_user.id)
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

    if not user.is_verified:
        raise HTTPException(403, 'Email not verified')

    user.set_last_login()
    await user.save()

    token = create_token(user.id)
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


@router.get(
    path='/verify/{token}'
)
async def verify_email(token: str):
    try:
        data = decode(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, 'Invalid token')

    if data.get('purpose') != 'verify':
        raise HTTPException(400, 'Invalid token')

    user = await User.find_one(User.id == data.get('user_id'))
    if not user:
        raise HTTPException(404, 'User not found')

    user.is_verified = True
    await user.save()

    return {'detail': 'Email verified successfully'}
