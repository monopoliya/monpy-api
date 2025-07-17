from config import config
from src.logger import get_logger

from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator

from botocore.exceptions import ClientError
from aiobotocore.session import get_session
from aiobotocore.client import AioBaseClient

logger = get_logger(__name__)


class S3Client:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region_name: str = 'eu-central-1'
    ):
        self.config = {
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
            'endpoint_url': f'https://s3.{region_name}.amazonaws.com',
            'region_name': region_name
        }

        self.session = get_session()
        self.bucket_name = bucket_name

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[AioBaseClient]:
        async with self.session.create_client('s3', **self.config) as client:
            yield client

    async def upload(
        self,
        bytes: bytes,
        filename: str,
        object_id: str,
        category: str = 'avatars',  # avatars, screenshots, etc.
        content_type: Optional[str] = None,
    ) -> None:
        if not (bytes and filename and object_id):
            raise ValueError('Fill in all the necessary parameters')

        # generate object key for s3 bucket
        object_name = f'{category}/{object_id}/{filename}'

        async with self.get_client() as client:
            try:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=bytes,
                    ContentType=content_type,
                    ContentDisposition='inline'
                )
            except ClientError as exc:
                logger.error(f'Failed to upload file'
                                f' {filename} to S3: {exc}')
                raise

        logger.info(f'File {filename} uploaded to '
                    f'{self.bucket_name}/{object_name}')

    async def list_objects(
        self,
        object_id: str,
        category: str = 'avatars'
    ) -> list[str]:
        # generate prefix for listing objects
        prefix = f'{category}/{object_id}/'

        async with self.get_client() as client:
            try:
                paginator = client.get_paginator('list_objects_v2')

                pages = paginator.paginate(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )

                keys: list[str] = []
                async for page in pages:
                    for obj in page.get('Contents', []):
                        keys.append(obj['Key'])
                return keys
            except ClientError as exc:
                logger.error(f'Failed to list objects '
                             f'with prefix {prefix}: {exc}')
                raise

    async def delete_object(
        self,
        object_id: str,
        filename: str,
        category: str = 'avatars'
    ) -> None:
        if not (object_id and filename):
            raise ValueError('Fill in all the necessary parameters')

        # generate object key for s3 bucket
        object_name = f'{category}/{object_id}/{filename}'

        async with self.get_client() as client:
            try:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
            except ClientError as exc:
                logger.error(f'Failed to delete file '
                             f'{filename} from S3: {exc}')
                raise

        logger.info(f'File {filename} deleted '
                    f'from {self.bucket_name}/{object_name}')


s3 = S3Client(
    config.aws_access_key,
    config.aws_secret_key,
    config.aws_bucket_name
)
