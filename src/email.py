import json
import resend
import aiohttp

from config import config
from src.logger import get_logger

logger = get_logger(__name__)

resend.api_key = config.resend_api_key
timeout = aiohttp.ClientTimeout(total=10)

try:
    _proxies_path = 'src/proxies.json'
    with open(_proxies_path, 'r', encoding='utf-8') as f:
        _proxies: list[str] = json.load(f)
except FileNotFoundError:
    _proxies = {}

_proxy_index = 0
_proxy_usage = 0


def _next_proxy() -> str | None:
    global _proxy_index, _proxy_usage
    if not _proxies:
        return None

    proxy = _proxies[_proxy_index]
    logger.debug(f'🔄 Using proxy: {proxy}')
    _proxy_usage += 1

    if _proxy_usage >= 3:
        _proxy_usage = 0
        _proxy_index = (_proxy_index + 1) % len(_proxies)

    return proxy


async def email_exists(email: str) -> bool:
    url = 'https://api.2ip.ua/email.json'

    async with aiohttp.ClientSession(
        timeout=timeout,  # need to add a proxy
    ) as session:
        try:
            params = {'email': email}
            async with session.get(
                url,
                params=params,
                proxy=_next_proxy()
            ) as response:
                text = await response.text()
                logger.debug('<<< quote raw response:\n%s', text)

                response.raise_for_status()
                data = await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f'[{e.status}][{e.message}] :: {e.request_info.url}')
            return False
        except aiohttp.ClientError as e:
            logger.error(e)
            return False

    return bool(data.get('exist'))


async def send_verification_email(email: str, token: str) -> None:
    if not (config.resend_sender and config.resend_api_key):
        logger.warning('Resend configuration is not set')
        return

    verify_link = f'http://127.0.0.1:8000/users/verify/{token}'

    html = (
        '<p>Please confirm your email by clicking '
        f'<a href="{verify_link}">here</a>.</p>'
    )

    params: resend.Emails.SendParams = {
        'from': config.resend_sender,
        'to': email,
        'subject': '✅ Confirm your email',
        'html': html
    }

    result: resend.Email = resend.Emails.send(params)
    return result
