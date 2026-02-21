from typing import Any

from testcontainers.core.container import DockerContainer

from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers.registry import PluginRegistry


class ContainerManager:
    """Manages container lifecycle for a single scenario."""

    def __init__(self) -> None:
        self._containers: dict[str, tuple[DockerContainer, Any]] = {}

    def start(self, plugin_name: str, **kwargs) -> Any:
        if plugin_name in self._containers:
            _, client = self._containers[plugin_name]
            return client

        plugin = PluginRegistry.get(plugin_name)
        container = plugin.create_container(**kwargs)
        container.start()
        plugin.on_start(container)
        client = plugin.get_client(container)
        self._containers[plugin_name] = (container, client)
        return client

    def get_client(self, plugin_name: str, **kwargs) -> Any:
        if plugin_name in self._containers:
            _, client = self._containers[plugin_name]
            return client
        return self.start(plugin_name, **kwargs)

    def stop_all(self) -> None:
        for plugin_name, (container, _) in self._containers.items():
            plugin = PluginRegistry.get(plugin_name)
            plugin.on_stop(container)
            container.stop()
        self._containers.clear()
