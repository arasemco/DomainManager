import os
from typing import Type, Dict, List, AnyStr, Tuple, Union

from src.providers.abstract import SubdomainProvider
from src.utils.logger import logger


class EnvironmentManager:
    @staticmethod
    def _get_variables(
            prefix: AnyStr,
            variables: Union[Tuple[AnyStr], List[AnyStr]],
            message: AnyStr = "required environment variables"
    ) -> Dict[AnyStr, AnyStr]:
        logger.debug(f"Fetching environment variables with prefix: {prefix}")
        result = {}
        for var in variables:
            env_value = os.getenv(f'{prefix}_{var}'.upper())
            logger.debug(f"Attempting to fetch variable: {prefix}_{var.upper()}")
            result[var] = env_value
            logger.debug(f"Fetched {prefix}_{var.upper()} = {env_value}")

        missing = [key for key, value in result.items() if not value]
        if missing:
            formatted_missing = ', '.join(missing)
            formatted_pattern = '\n'.join([f'{prefix}_{key}'.upper() for key in missing])
            logger.error(f"Missing {message}: {formatted_missing}")
            raise ValueError(
                f"Missing {message}: {formatted_missing}.\n"
                f"Please ensure you set the environment variables as shown below:\n{formatted_pattern}"
            )
        logger.info(f"Successfully fetched environment variables with prefix: {prefix}")
        return result

    @classmethod
    def get_provider_keys(cls, provider: Type[SubdomainProvider]) -> Dict[AnyStr, AnyStr]:
        logger.debug(f"Getting provider keys for provider: {provider.__name__}")
        keys = cls._get_variables(
            prefix=f'DNM_{provider.__name__.replace("Provider", "").upper()}',
            variables=provider.keys,
            message=f"API keys for provider '{provider.name}'"
        )
        logger.info(f"Successfully fetched provider keys for provider: {provider.__name__}")
        return keys

    @classmethod
    def get_provider_details(cls, provider: Type[SubdomainProvider]) -> Dict[AnyStr, AnyStr]:
        logger.debug(f"Getting provider details for provider: {provider.__name__}")
        details = cls._get_variables(
            prefix='DNM',
            variables=provider.details,
            message="domain details"
        )
        logger.info(f"Successfully fetched provider details for provider: {provider.__name__}")
        return details

    @classmethod
    def get_docker_configuration(cls, variables: Union[Tuple[AnyStr], List[AnyStr]]) -> Dict[AnyStr, AnyStr]:
        logger.debug(f"Getting Docker configuration for variables: {variables}")
        config = cls._get_variables(
            prefix='DNM_DOCKER',
            variables=variables,
            message="Docker configuration"
        )
        logger.info("Successfully fetched Docker configuration")
        return config
