# Utility Functions
from typing import Optional, AnyStr

import validators

from src.exceptions.custom_exceptions import InvalidDomainException


def validate_domain(name: AnyStr):
    if not validators.domain(name):
        raise InvalidDomainException(f"The domain name '{name}' is not valid.")
    return name


def extract_subdomain(full_domain: AnyStr, base_domain: AnyStr) -> Optional[AnyStr]:
    if not validators.hostname(full_domain) or not validators.hostname(base_domain):
        return None

    full_domain_parts = full_domain.split('.')
    base_domain_parts = base_domain.split('.')

    if full_domain_parts[-len(base_domain_parts):] == base_domain_parts:
        subdomain_parts = full_domain_parts[:-len(base_domain_parts)]
        return '.'.join(subdomain_parts) if subdomain_parts else None

    elif len(full_domain_parts) == 1:
        return full_domain

    return None

