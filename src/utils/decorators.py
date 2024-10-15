import ovh
import requests
import functools

from src.utils.logger import logger


def handle_api_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ovh.exceptions.APIError, requests.RequestException) as exception:
            response = getattr(exception, 'response', None)
            if hasattr(response, 'status_code') and hasattr(response, 'url'):
                logger.error(f"API Error {response.status_code}: {response.url}")
            else:
                logger.error(f"Unexpected Error: {exception}")
    return wrapper
