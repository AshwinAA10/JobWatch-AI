"""Lightweight registry for career portal connector classes."""

from typing import Dict, List, Type
from app.connectors.base import BaseJobConnector
from app.connectors.exceptions import UnsupportedConnectorError


class ConnectorRegistry:
    """Registry maintaining mappings between source_type strings and connector classes."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[BaseJobConnector]] = {}

    def register(self, source_type: str, connector_cls: Type[BaseJobConnector]) -> None:
        """Register a connector class under a source_type key."""
        key = source_type.lower().strip()
        self._registry[key] = connector_cls

    def get(self, source_type: str) -> Type[BaseJobConnector]:
        """Look up a connector class by source_type."""
        key = source_type.lower().strip() if source_type else ""
        if key not in self._registry:
            supported = ", ".join(sorted(self._registry.keys())) or "none"
            raise UnsupportedConnectorError(
                f"Unsupported career source type: '{source_type}'. Supported providers: [{supported}]",
                source_type=source_type,
            )
        return self._registry[key]

    def is_supported(self, source_type: str) -> bool:
        """Check whether a source_type has a registered connector."""
        key = source_type.lower().strip() if source_type else ""
        return key in self._registry

    def list_supported(self) -> List[str]:
        """Return a sorted list of all supported source_type identifiers."""
        return sorted(list(self._registry.keys()))


# Global default registry instance
registry = ConnectorRegistry()
