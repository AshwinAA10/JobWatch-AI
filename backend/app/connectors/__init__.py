"""Career portal and job board connector integration layer for JobWatch AI (Phase 2)."""

from app.connectors.base import BaseJobConnector
from app.connectors.exceptions import (
    ConnectorConfigurationError,
    ConnectorError,
    ConnectorParseError,
    ConnectorRateLimitError,
    ConnectorRequestError,
    ConnectorResponseError,
    UnsupportedConnectorError,
)
from app.connectors.factory import ConnectorFactory
from app.connectors.greenhouse.connector import GreenhouseConnector
from app.connectors.http import ConnectorHttpClient
from app.connectors.lever.connector import LeverConnector
from app.connectors.models import NormalizedJob
from app.connectors.registry import ConnectorRegistry, registry
from app.connectors.workday.connector import WorkdayConnector

# Register supported connectors in default registry
registry.register("greenhouse", GreenhouseConnector)
registry.register("lever", LeverConnector)
registry.register("workday", WorkdayConnector)

__all__ = [
    "BaseJobConnector",
    "NormalizedJob",
    "ConnectorFactory",
    "ConnectorRegistry",
    "registry",
    "ConnectorHttpClient",
    "GreenhouseConnector",
    "LeverConnector",
    "WorkdayConnector",
    "ConnectorError",
    "ConnectorConfigurationError",
    "UnsupportedConnectorError",
    "ConnectorRequestError",
    "ConnectorResponseError",
    "ConnectorParseError",
    "ConnectorRateLimitError",
]
