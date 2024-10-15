from abc import ABC, abstractmethod
from typing import AnyStr, Dict, Type, Tuple

from src.utils.logger import logger
from src.utils.validators import validate_domain


class APIBaseProvider:
    name: AnyStr
    keys: Tuple[AnyStr]
    details: Tuple[AnyStr] = ('domain_name', 'target')
    _providers: Dict[AnyStr, Type['APIBaseProvider']] = {}

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.name = cls.__name__.replace('Provider', '')
        APIBaseProvider._providers[cls.name.upper()] = cls

    def __init__(self, domain_name: AnyStr, target: AnyStr):
        self.domain_name = validate_domain(domain_name)
        self.target = validate_domain(target)

    def _log_action(self, action: AnyStr, subdomain: AnyStr):
        logger.info(f"{action} subdomain '{subdomain}' on '{self.name}' for domain '{self.domain_name}' with target '{self.target}'.")


class SubdomainProvider(ABC, APIBaseProvider):
    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def add_subdomain(self, subdomain: str):
        pass

    @abstractmethod
    def remove_subdomain(self, subdomain: str):
        pass
