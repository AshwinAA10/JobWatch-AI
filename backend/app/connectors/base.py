"""Abstract base class for all career portal connectors."""

from abc import ABC, abstractmethod
from typing import List, Optional
import httpx

from app.connectors.http import ConnectorHttpClient
from app.connectors.models import NormalizedJob
from app.models.career_source import CareerSource


class BaseJobConnector(ABC):
    """Unified interface that all career portal connectors must implement.
    
    The monitoring engine interacts solely through this contract, insulating
    the rest of the platform from provider-specific formats or transport details.
    """

    source_type: str = "base"

    def __init__(
        self,
        source: CareerSource,
        http_client: Optional[ConnectorHttpClient] = None,
        raw_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.source = source
        if http_client is not None:
            self.http = http_client
        else:
            self.http = ConnectorHttpClient(
                client=raw_client,
                source_type=self.source_type,
            )
        from app.connectors.http import validate_url
        validate_url(self.source.base_url, source_type=self.source_type)
        self.validate_source_config()

    @abstractmethod
    def validate_source_config(self) -> None:
        """Validate that the CareerSource provides all required parameters for this provider.
        
        Raises:
            ConnectorConfigurationError: If base_url, tokens, or options are malformed.
        """
        pass

    @abstractmethod
    async def fetch_jobs(self) -> List[NormalizedJob]:
        """Retrieve and normalize all currently open jobs for the configured career source.
        
        Returns:
            List of NormalizedJob instances.
        
        Raises:
            ConnectorConfigurationError: On invalid board or authentication failure.
            ConnectorRequestError: On network or transport failures.
            ConnectorResponseError: On provider error responses.
            ConnectorParseError: On corrupt payloads.
        """
        pass

    async def aclose(self) -> None:
        """Clean up underlying HTTP client resources."""
        await self.http.close()
