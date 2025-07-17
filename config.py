from typing import Optional
from pydantic_settings import BaseSettings


ALLOWED_DOMAINS = [
    'gmail.com',
    'outlook.com',
    'mail.ru',
    'yandex.ru',
    'yahoo.com',
    'hotmail.com',
    'icloud.com'
]


ALLOWED_FILE_EXTS = [
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.webp'
]


class Config(BaseSettings):
    debug: bool = False

    # beanie (MongoDB ODM)
    mongo_uri: str = 'mongodb://localhost:27017/'

    # redis (conf)
    redis_uri: Optional[str] = None

    # origins for CORS
    allowed_origin: Optional[str] = '*'

    # jwt secret key
    jwt_secret: str = 'your-jwt-secret-key'

    # resend conf
    resend_sender: Optional[str] = 'support@monopoliya.fun'
    resend_api_key: Optional[str] = None

    # AWS S3 conf
    aws_region_name: str = 'eu-central-1'
    aws_bucket_name: str = 'cdn.monopoliya.fun'

    aws_access_key: str
    aws_secret_key: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'


config = Config()
