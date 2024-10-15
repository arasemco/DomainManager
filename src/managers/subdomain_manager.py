from src.utils.logger import logger
from src.utils.validators import extract_subdomain
from src.providers.abstract import SubdomainProvider


class SubdomainManager:
    def __init__(self, provider: SubdomainProvider):
        self.provider = provider

    def add_subdomain(self, full_domain: str):
        subdomain = extract_subdomain(full_domain, self.provider.domain_name)
        if subdomain:
            self.provider.add_subdomain(subdomain)
        else:
            logger.error(f"Invalid subdomain '{full_domain}' for domain '{self.provider.domain_name}'.")

    def remove_subdomain(self, full_domain: str):
        subdomain = extract_subdomain(full_domain, self.provider.domain_name)
        if subdomain:
            self.provider.remove_subdomain(subdomain)
        else:
            logger.error(f"Invalid subdomain '{full_domain}' for domain '{self.provider.domain_name}'.")
