from config import config
from src.cache import init_redis

import os
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from beanie import init_beanie
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient


@asynccontextmanager
async def lifespan(_: FastAPI):
    client = AsyncIOMotorClient(config.mongo_uri)
    await init_beanie(database=client.monopoly, document_models=[
        # Add your Beanie document models here
    ])

    if config.redis_uri:
        # Initialize Redis if a URI is provided
        await init_redis(config.redis_uri)

    yield

    client.close()  # close MongoDB connection


app = FastAPI(
    lifespan=lifespan,
    debug=config.debug,
    title='Monopoly Game API',
    description='API For the Monopoly Game Server',
    docs_url='/docs' if config.debug else None,
    redoc_url='/redoc' if config.debug else None
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 8000))
    HOST = '127.0.0.1' if config.debug else '0.0.0.0'
    uvicorn.run('main:app', host=HOST, port=PORT, reload=config.debug)
