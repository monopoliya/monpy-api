import jwt
import hashlib

import mimetypes
from pathlib import Path

from .models import User
from .forms import UserCreate, UserLogin
from .public import UserPublic, AuthResponse

from src.services.s3client import s3
from src.services.snowflake import Snowflake
from config import ALLOWED_DOMAINS, ALLOWED_FILE_EXTS

from src.apps.depends import login_required
from src.apps.security import create_token, decode
from src.services.email import email_exists, send_verification_email

from fastapi import APIRouter, Request, \
    UploadFile, Depends, HTTPException

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

    # generate a unique user ID
    # using Snowflake ID generator
    user_id = Snowflake.generate()

    # hash the password for security
    hashed = hashlib.md5(user.password.encode()).hexdigest()

    new_user = User(
        id=user_id,
        name=user.name,
        email=user.email,
        password=hashed
    )

    new_user.set_last_login()
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
async def get_me(payload: dict = Depends(login_required)):
    user = await User.find_one(User.id == payload['user_id'])
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

    user = await User.get(data['user_id'])
    if not user:
        raise HTTPException(404, 'User not found')

    user.is_verified = True
    await user.save()

    return {'detail': 'Email verified successfully'}


@router.patch(
    path='/avatar',
    response_model=dict
)
async def update_avatar(
    request: Request,
    upl: UploadFile,
    payload: dict = Depends(login_required)
):
    max_size = 3 * 1024 * 1024  # 3MB in bytes
    if upl.size and upl.size > max_size:
        raise HTTPException(400, 'File size exceeds limit of 3MB')

    ext = Path(upl.filename).suffix.lower()
    if ext not in ALLOWED_FILE_EXTS:
        raise HTTPException(400, f'Invalid file extension: {ext}')

    file_bytes = await upl.read()
    content_type, _ = mimetypes.guess_type(upl.filename)

    user_id = str(payload['user_id'])
    hashed_name = hashlib.md5(user_id.encode()).hexdigest()

    hashed_filename = f'{hashed_name}{ext}'

    try:
        keys = await s3.list_objects(
            object_id=user_id, category='avatars'
        )

        for key in keys:
            old_file = Path(key).name
            # skip if the file is the same
            if old_file != hashed_filename:
                await s3.delete_object(
                    object_id=user_id,
                    filename=old_file,
                    category='avatars'
                )

    except Exception:
        # Log but don't block upload
        pass

    await s3.upload(
        bytes=file_bytes,
        filename=hashed_filename,
        object_id=user_id,
        content_type=content_type,
        category='avatars'
    )

    user = await User.get(user_id)
    if not user:
        raise HTTPException(404, 'User not found')

    # save avatar key in db
    user.avatar = hashed_filename
    await user.save()

    # construct URL dynamically
    base_url = 'https://cdn.monopoliya.fun'
    avatar_url = f'{base_url}/avatars/{user_id}/{hashed_filename}'

    return {'url': avatar_url}
