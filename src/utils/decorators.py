import ovh
import requests
import functools

from src.utils.logger import logger


def handle_api_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling function '{func.__name__}' with args: {args} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function '{func.__name__}' executed successfully with result: {result}")
            return result
        except (ovh.exceptions.APIError, requests.RequestException) as exception:
            response = getattr(exception, 'response', None)
            if response is not None and hasattr(response, 'status_code') and hasattr(response, 'url'):
                logger.error(f"API Error {response.status_code}: {response.url}")
            else:
                logger.error(f"Unexpected Error: {exception}")
    return wrapper
