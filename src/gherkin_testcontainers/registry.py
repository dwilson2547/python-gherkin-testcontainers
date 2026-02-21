from importlib.metadata import entry_points

from gherkin_testcontainers.plugin import ContainerPlugin


class PluginRegistry:
    """Discovers and stores container plugins."""

    _plugins: dict[str, type[ContainerPlugin]] = {}
    _discovered: bool = False

    @classmethod
    def register(cls, name: str, plugin_class: type[ContainerPlugin]) -> None:
        cls._plugins[name] = plugin_class

    @classmethod
    def get(cls, name: str) -> ContainerPlugin:
        if not cls._discovered:
            cls.discover()
        if name not in cls._plugins:
            raise KeyError(
                f"Plugin '{name}' not found. "
                f"Available: {list(cls._plugins.keys())}"
            )
        return cls._plugins[name]()

    @classmethod
    def discover(cls) -> None:
        cls._discovered = True
        for ep in entry_points(group="gherkin_testcontainers.plugins"):
            cls._plugins[ep.name] = ep.load()
