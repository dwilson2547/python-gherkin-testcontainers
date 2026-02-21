import pytest
from unittest.mock import MagicMock, patch
from gherkin_testcontainers.manager import ContainerManager
from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers.registry import PluginRegistry


class FakePlugin(ContainerPlugin):
    @property
    def name(self) -> str:
        return "fake"

    def create_container(self, **kwargs):
        container = MagicMock()
        container._kwargs = kwargs
        return container

    def get_client(self, container):
        return MagicMock(name="fake_client")

    def on_start(self, container):
        container.on_start_called = True

    def on_stop(self, container):
        container.on_stop_called = True


@pytest.fixture(autouse=True)
def clean_registry():
    PluginRegistry._plugins.clear()
    PluginRegistry.register("fake", FakePlugin)
    yield
    PluginRegistry._plugins.clear()


def test_start_creates_and_starts_container():
    manager = ContainerManager()
    client = manager.start("fake")
    assert client is not None


def test_get_client_returns_existing_client():
    manager = ContainerManager()
    client1 = manager.start("fake")
    client2 = manager.get_client("fake")
    assert client1 is client2


def test_get_client_starts_container_if_not_running():
    manager = ContainerManager()
    client = manager.get_client("fake")
    assert client is not None


def test_start_passes_kwargs_to_plugin():
    manager = ContainerManager()
    manager.start("fake", image="custom:latest")
    container, _ = manager._containers["fake"]
    assert container._kwargs == {"image": "custom:latest"}


def test_stop_all_stops_containers_and_calls_hooks():
    manager = ContainerManager()
    manager.start("fake")
    container, _ = manager._containers["fake"]
    manager.stop_all()
    container.stop.assert_called_once()
    assert len(manager._containers) == 0


def test_stop_all_on_empty_manager():
    manager = ContainerManager()
    manager.stop_all()  # should not raise
