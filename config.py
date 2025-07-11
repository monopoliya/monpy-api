from typing import Optional
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    debug: bool = False

    # beanie (MongoDB ODM)
    mongo_uri: str = 'mongodb://localhost:27017/'

    # redis (configuration)
    redis_uri: Optional[str] = None

    # origins for CORS
    allowed_origin: Optional[str] = '*'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'


config = Config()
