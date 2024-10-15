from src.utils.logger import logger
from src.utils.validators import extract_subdomain
from src.providers.abstract import SubdomainProvider


class SubdomainManager:
    def __init__(self, provider: SubdomainProvider):
        logger.debug(f"Initializing SubdomainManager with provider: {provider.__class__.__name__}")
        self.provider = provider
        logger.info(f"SubdomainManager initialized with provider: {provider.__class__.__name__}")

    def add_subdomain(self, full_domain: str):
        logger.debug(f"Attempting to add subdomain for full domain: {full_domain}")
        subdomain = extract_subdomain(full_domain, self.provider.domain_name)
        if subdomain:
            logger.info(f"Adding subdomain: {subdomain} to provider: {self.provider.domain_name}")
            try:
                logger.debug(f"Calling provider's add_subdomain method for subdomain: {subdomain}")
                self.provider.add_subdomain(subdomain)
                logger.info(f"Successfully added subdomain: {subdomain}")
            except Exception as e:
                logger.error(f"Failed to add subdomain '{subdomain}': {e}")
        else:
            logger.error(f"Invalid subdomain '{full_domain}' for domain '{self.provider.domain_name}'.")

    def remove_subdomain(self, full_domain: str):
        logger.debug(f"Attempting to remove subdomain for full domain: {full_domain}")
        subdomain = extract_subdomain(full_domain, self.provider.domain_name)
        if subdomain:
            logger.info(f"Removing subdomain: {subdomain} from provider: {self.provider.domain_name}")
            try:
                logger.debug(f"Calling provider's remove_subdomain method for subdomain: {subdomain}")
                self.provider.remove_subdomain(subdomain)
                logger.info(f"Successfully removed subdomain: {subdomain}")
            except Exception as e:
                logger.error(f"Failed to remove subdomain '{subdomain}': {e}")
        else:
            logger.error(f"Invalid subdomain '{full_domain}' for domain '{self.provider.domain_name}'.")
