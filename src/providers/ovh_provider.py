import time
import random

import ovh

from src.utils.logger import logger
from src.utils.decorators import handle_api_errors
from src.providers.abstract import SubdomainProvider


class OVHProvider(SubdomainProvider):
    keys = ('application_key', 'application_secret', 'consumer_key')

    def __init__(self, application_key, application_secret, consumer_key, domain_name, target):
        logger.debug(f"Initializing OVHProvider with domain: {domain_name} and target: {target}")
        super().__init__(domain_name, target)
        self._application_key = application_key
        self._application_secret = application_secret
        self._consumer_key = consumer_key

        self.client = None
        self.authenticate()
        logger.info(f"OVHProvider initialized for domain: {domain_name}")

    def authenticate(self):
        logger.debug(f"Authenticating OVH provider for domain: {self.domain_name}")
        self.client = ovh.Client(
            endpoint='ovh-eu',
            application_key=self._application_key,
            application_secret=self._application_secret,
            consumer_key=self._consumer_key
        )
        logger.info("OVH provider authenticated successfully.")

    @handle_api_errors
    def add_subdomain(self, subdomain: str):
        logger.debug(f"Attempting to add subdomain: {subdomain} to domain: {self.domain_name}")
        try:
            self.client.post(f'/domain/zone/{self.domain_name}/record',
                             fieldType='CNAME',
                             subDomain=subdomain,
                             target=self.target,
                             ttl=3600)
            logger.info(f"Successfully added subdomain: {subdomain} to domain: {self.domain_name}")
            self._log_action(action="Added", subdomain=subdomain)
        except ovh.exceptions.APIError as e:
            logger.error(f"Failed to add subdomain '{subdomain}' to domain '{self.domain_name}': {e}")

    @handle_api_errors
    def remove_subdomain(self, subdomain: str):
        logger.debug(f"Attempting to remove subdomain: {subdomain} from domain: {self.domain_name}")
        try:
            records = self.client.get(f'/domain/zone/{self.domain_name}/record',
                                      fieldType='CNAME',
                                      subDomain=subdomain)
            if not records:
                logger.error(f"No records found for subdomain '{subdomain}' in domain '{self.domain_name}'")
                return

            for record_id in records:
                logger.debug(f"Deleting record ID: {record_id} for subdomain: {subdomain}")
                self.client.delete(f'/domain/zone/{self.domain_name}/record/{record_id}')
                delay = random.uniform(a=0.1, b=0.5)
                logger.debug(f"Sleeping for {delay} seconds before deleting the next record (if any)")
                time.sleep(delay)

            logger.info(f"Successfully removed subdomain: {subdomain} from domain: {self.domain_name}")
            self._log_action(action="Removed", subdomain=subdomain)
        except ovh.exceptions.APIError as e:
            logger.error(f"Failed to remove subdomain '{subdomain}' from domain '{self.domain_name}': {e}")
