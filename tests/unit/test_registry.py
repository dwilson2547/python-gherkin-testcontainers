import pytest
from unittest.mock import MagicMock, patch
from gherkin_testcontainers.registry import PluginRegistry
from gherkin_testcontainers.plugin import ContainerPlugin


class FakePlugin(ContainerPlugin):
    @property
    def name(self) -> str:
        return "fake"

    def create_container(self, **kwargs):
        return MagicMock()

    def get_client(self, container):
        return MagicMock()


@pytest.fixture(autouse=True)
def clean_registry():
    """Reset registry state between tests."""
    PluginRegistry._plugins.clear()
    PluginRegistry._discovered = False
    yield
    PluginRegistry._plugins.clear()
    PluginRegistry._discovered = False


def test_register_and_get_plugin():
    PluginRegistry.register("fake", FakePlugin)
    plugin = PluginRegistry.get("fake")
    assert isinstance(plugin, FakePlugin)
    assert plugin.name == "fake"


def test_get_unknown_plugin_raises():
    with pytest.raises(KeyError, match="no_such_plugin"):
        PluginRegistry.get("no_such_plugin")


def test_discover_loads_entry_points():
    mock_ep = MagicMock()
    mock_ep.name = "fake"
    mock_ep.load.return_value = FakePlugin

    with patch(
        "gherkin_testcontainers.registry.entry_points",
        return_value=[mock_ep],
    ):
        PluginRegistry.discover()

    plugin = PluginRegistry.get("fake")
    assert isinstance(plugin, FakePlugin)
