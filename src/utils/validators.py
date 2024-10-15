from typing import Optional, AnyStr

import validators

from src.exceptions.custom_exceptions import InvalidDomainException
from src.utils.logger import logger


def validate_domain(name: AnyStr):
    logger.debug(f"Validating domain name: {name}")
    if not validators.domain(name):
        logger.error(f"Invalid domain name: {name}")
        raise InvalidDomainException(f"The domain name '{name}' is not valid.")
    logger.info(f"Domain name '{name}' is valid.")
    return name


def extract_subdomain(full_domain: AnyStr, base_domain: AnyStr) -> Optional[AnyStr]:
    logger.debug(f"Extracting subdomain from full_domain: {full_domain}, base_domain: {base_domain}")
    if not validators.hostname(full_domain) or not validators.domain(base_domain):
        logger.error(f"Invalid hostname in full_domain: {full_domain} or base_domain: {base_domain}")
        return None

    full_domain_parts = full_domain.split('.')
    base_domain_parts = base_domain.split('.')

    if full_domain_parts[-len(base_domain_parts):] == base_domain_parts:
        subdomain_parts = full_domain_parts[:-len(base_domain_parts)]
        subdomain = '.'.join(subdomain_parts) if subdomain_parts else None
        logger.info(f"Extracted subdomain: {subdomain}")
        return subdomain

    elif len(full_domain_parts) == 1:
        logger.info(f"Full domain is a single part: {full_domain}")
        return full_domain

    logger.debug(f"No subdomain extracted from full_domain: {full_domain}")
    return None
