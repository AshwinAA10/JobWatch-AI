"""Connector factory for resolving and instantiating provider connectors."""

from typing import Optional
import httpx

from app.connectors.base import BaseJobConnector
from app.connectors.http import ConnectorHttpClient
from app.connectors.registry import registry
from app.models.career_source import CareerSource


class ConnectorFactory:
    """Factory responsible for instantiating the appropriate connector for a CareerSource."""

    @classmethod
    def create(
        cls,
        source: CareerSource,
        http_client: Optional[ConnectorHttpClient] = None,
        raw_client: Optional[httpx.AsyncClient] = None,
    ) -> BaseJobConnector:
        """Instantiate a connector matching the source's source_type.
        
        Args:
            source: The CareerSource database model instance.
            http_client: Optional pre-configured ConnectorHttpClient.
            raw_client: Optional raw httpx.AsyncClient instance.
            
        Returns:
            An initialized instance of BaseJobConnector.
        """
        connector_cls = registry.get(source.source_type)
        return connector_cls(
            source=source,
            http_client=http_client,
            raw_client=raw_client,
        )
