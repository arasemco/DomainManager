# Environment Handler
import os
from typing import Type, Dict, List, AnyStr, Tuple, Union

from src.providers.abstract import SubdomainProvider


class EnvironmentManager:
    @staticmethod
    def _get_variables(
            prefix: AnyStr,
            variables: Union[Tuple[AnyStr], List[AnyStr]],
            message: AnyStr = "required environment variables"
    ) -> Dict[AnyStr, AnyStr]:
        result = {}
        for var in variables:
            result[var] = os.getenv(key=f'{prefix}_{var}'.upper(), default=None)

        missing = [key for key, value in result.items() if not value]
        if missing:
            formatted_missing = ', '.join(missing)
            formatted_pattern = '\n'.join([f'{prefix}_{key}'.upper() for key in missing])
            raise ValueError(
                f"Missing {message}: {formatted_missing}.\n"
                f"Please ensure you set the environment variables as shown below:\n{formatted_pattern}"
            )
        return result

    @classmethod
    def get_provider_keys(cls, provider: Type[SubdomainProvider]) -> Dict[AnyStr, AnyStr]:
        return cls._get_variables(
            prefix=f'DNM_{provider.__name__.replace("Provider", "").upper()}',
            variables=provider.keys,
            message=f"API keys for provider '{provider.name}'"
        )

    @classmethod
    def get_provider_details(cls, provider: Type[SubdomainProvider]) -> Dict[AnyStr, AnyStr]:
        return cls._get_variables(
            prefix='DNM',
            variables=provider.details,
            message="domain details"
        )

    @classmethod
    def get_docker_configuration(cls, variables: Union[Tuple[AnyStr], List[AnyStr]]) -> Dict[AnyStr, AnyStr]:
        return cls._get_variables(
            prefix='DNM_DOCKER',
            variables=variables,
            message="Docker configuration"
        )
