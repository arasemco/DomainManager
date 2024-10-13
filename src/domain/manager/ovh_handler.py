import ovh
from src.utils.logger import logger
from src.domain.manager.base import DomainManager

class OVHDomainManager(DomainManager):
    def __init__(self, domain, target, application_credential, field_type='CNAME'):
        super().__init__(domain, target, field_type)
        self.client = ovh.Client(
            endpoint='ovh-eu',  # Change this to 'ovh-us' or your appropriate region if needed
            **application_credential
        )
        self._validate_domain()

    def _validate_domain(self):
        try:
            self.zone = self.client.get(f"/domain/zone/{self.domain}")

        except ovh.exceptions.ResourceNotFoundError:
            domains = self.client.get(f"/domain/zone")
            raise TypeError(f"The domain '{self.domain}' does not exist! Available domains: {domains}")

    def create_subdomain(self, subdomain, ttl=0):
        full_domain = f"{subdomain}.{self.domain}"
        try:
            response = self.client.post(
                f'/domain/zone/{self.domain}/record',
                fieldType=self.field_type,
                subDomain=subdomain,
                target=self.target,
                ttl=ttl
            )
            logger.info(f"Subdomain {full_domain} created: {response}")

        except ovh.exceptions.APIError as e:
            self.handle_api_error("create", full_domain, e)

    def remove_subdomain(self, subdomain):
        full_domain = f"{subdomain}.{self.domain}"
        try:
            records = self.client.get(
                f'/domain/zone/{self.domain}/record',
                fieldType=self.field_type,
                subDomain=subdomain
            )
            for record in records:
                self.client.delete(f'/domain/zone/{self.domain}/record/{record}')
            logger.info(f"Subdomain {full_domain} removed: {records}")

        except ovh.exceptions.APIError as e:
            self.handle_api_error("remove", full_domain, e)
