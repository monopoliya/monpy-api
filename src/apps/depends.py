from src.jwt import decode
from src.logger import get_logger

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, \
    HTTPAuthorizationCredentials

# initialize the logger
logger = get_logger(__name__)
# initialize the HTTPBearer security scheme
http_bearer = HTTPBearer(auto_error=False)


def login_required(
    header: HTTPAuthorizationCredentials = Depends(http_bearer)  # noqa: B008
) -> str:
    if not (header and header.scheme and header.credentials):
        raise HTTPException(403, 'Forbidden')

    if header.scheme.lower() != 'bearer':
        raise HTTPException(403, 'Forbidden')

    payload = decode(header.credentials)
    return payload


def get_user_id(payload: str = Depends(login_required)) -> int:
    if not payload or 'user_id' not in payload:
        raise HTTPException(403, 'Forbidden')

    user_id = payload['user_id']
    if not isinstance(user_id, int):
        user_id = int(user_id)

    return user_id
