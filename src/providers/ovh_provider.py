import time
import random

import ovh

from src.utils.decorators import handle_api_errors
from src.providers.abstract import SubdomainProvider


class OVHProvider(SubdomainProvider):
    keys = ('application_key', 'application_secret', 'consumer_key')

    def __init__(self, application_key, application_secret, consumer_key, domain_name, target):
        super().__init__(domain_name, target)
        self._application_key = application_key
        self._application_secret = application_secret
        self._consumer_key = consumer_key

        self.client = None
        self.authenticate()

    def authenticate(self):
        self.client = ovh.Client(
            endpoint='ovh-eu',
            application_key=self._application_key,
            application_secret=self._application_secret,
            consumer_key=self._consumer_key
        )

    @handle_api_errors
    def add_subdomain(self, subdomain: str):
        self.client.post(f'/domain/zone/{self.domain_name}/record',
                         fieldType='CNAME',
                         subDomain=subdomain,
                         target=self.target,
                         ttl=3600)
        self._log_action(action="Added", subdomain=subdomain)

    @handle_api_errors
    def remove_subdomain(self, subdomain: str):
        records = self.client.get(f'/domain/zone/{self.domain_name}/record',
                                  fieldType='CNAME',
                                  subDomain=subdomain)
        for record_id in records:
            self.client.delete(f'/domain/zone/{self.domain_name}/record/{record_id}')
            delay = random.uniform(a=0.1, b=0.5)
            time.sleep(delay)

        self._log_action(action="Removed", subdomain=subdomain)
