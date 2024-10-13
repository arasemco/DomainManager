from src.utils.logger import logger


class DomainManager:
    def __init__(self, domain, target, field_type='CNAME'):
        self.domain = domain
        self.target = target
        self.field_type = field_type
        self.domain_parts = self.domain.split('.')
        self.domain_length = len(self.domain_parts)

    def get_record(self, record: str = None):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def create_subdomain(self, subdomain, ttl=0):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def remove_subdomain(self, subdomain):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def handle_api_error(self, action, full_domain, error):
        logger.error(f"[{type(self).__name__}] Failed to {action} subdomain {full_domain}: {str(error)}")

    def extract_subdomain(self, full_domain):
        full_domain_parts = full_domain.split('.')
        if full_domain_parts[-self.domain_length:] == self.domain_parts:
            return '.'.join(full_domain_parts[:-self.domain_length])

        elif len(full_domain_parts) == 1:
            return full_domain

        return None
