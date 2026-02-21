from abc import ABC, abstractmethod
from typing import Any

from testcontainers.core.container import DockerContainer


class ContainerPlugin(ABC):
    """Base class for all container plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier, e.g. 'postgres'."""

    @abstractmethod
    def create_container(self, **kwargs) -> DockerContainer:
        """Create and configure a testcontainer instance."""

    @abstractmethod
    def get_client(self, container: DockerContainer) -> Any:
        """Return a raw client/connection from a running container."""

    def on_start(self, container: DockerContainer) -> None:
        """Optional hook called after container starts."""

    def on_stop(self, container: DockerContainer) -> None:
        """Optional hook called before container stops."""
