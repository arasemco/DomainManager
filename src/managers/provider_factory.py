from typing import Dict, Type

from src.config.environment import EnvironmentManager
from src.providers import SubdomainProvider


class ProviderFactory:
    # TODO: Somme how implement this class to be full manager of providers with auto registration
    # And place it in managers package
    # _providers: Dict[str, type[SubdomainProvider]] = {}
    _providers: Dict[str, type[SubdomainProvider]] = SubdomainProvider._providers

    @classmethod
    def register_provider(cls, name: str, provider_cls):
        cls._providers[name.upper()] = provider_cls

    @classmethod
    def get_provider(cls, name) -> SubdomainProvider:
        provider_cls = cls._providers.get(name.upper())
        if not provider_cls:
            raise ValueError(f"Provider '{name}' is not registered.")

        keys = EnvironmentManager.get_provider_keys(provider_cls)
        domain_details = EnvironmentManager.get_provider_details(provider_cls)
        return provider_cls(**keys, **domain_details)
