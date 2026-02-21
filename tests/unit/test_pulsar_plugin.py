# tests/unit/test_pulsar_plugin.py
from unittest.mock import MagicMock, patch

from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers_pulsar.plugin import (
    DEFAULT_PULSAR_IMAGE,
    PULSAR_BINARY_PORT,
    PULSAR_HTTP_PORT,
    PulsarContainer,
    PulsarPlugin,
)


def test_pulsar_plugin_is_a_container_plugin():
    plugin = PulsarPlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_pulsar_plugin_name():
    plugin = PulsarPlugin()
    assert plugin.name == "pulsar"


def test_pulsar_plugin_create_container_returns_pulsar_container():
    plugin = PulsarPlugin()
    container = plugin.create_container()
    assert isinstance(container, PulsarContainer)


def test_pulsar_plugin_create_container_custom_image():
    plugin = PulsarPlugin()

    with patch("gherkin_testcontainers_pulsar.plugin.PulsarContainer") as MockContainer:
        plugin.create_container(image="apachepulsar/pulsar:2.11.0")
        MockContainer.assert_called_once_with(image="apachepulsar/pulsar:2.11.0")


def test_pulsar_container_default_image():
    with patch("gherkin_testcontainers_pulsar.plugin.DockerContainer.__init__", return_value=None):
        with patch.object(PulsarContainer, "with_command"):
            with patch.object(PulsarContainer, "with_exposed_ports"):
                container = PulsarContainer.__new__(PulsarContainer)
                # Just verify the default image constant is correct
                assert DEFAULT_PULSAR_IMAGE == "apachepulsar/pulsar:3.0.0"


def test_pulsar_container_get_broker_url():
    container = MagicMock(spec=PulsarContainer)
    container.get_container_host_ip.return_value = "localhost"
    container.get_exposed_port.return_value = "16650"
    container.get_broker_url = PulsarContainer.get_broker_url.__get__(container)

    url = container.get_broker_url()

    container.get_exposed_port.assert_called_once_with(PULSAR_BINARY_PORT)
    assert url == "pulsar://localhost:16650"


def test_pulsar_container_get_admin_url():
    container = MagicMock(spec=PulsarContainer)
    container.get_container_host_ip.return_value = "localhost"
    container.get_exposed_port.return_value = "18080"
    container.get_admin_url = PulsarContainer.get_admin_url.__get__(container)

    url = container.get_admin_url()

    container.get_exposed_port.assert_called_once_with(PULSAR_HTTP_PORT)
    assert url == "http://localhost:18080"


def test_pulsar_plugin_get_client_returns_pulsar_client():
    plugin = PulsarPlugin()
    mock_container = MagicMock()
    mock_container.get_broker_url.return_value = "pulsar://localhost:6650"

    with patch("pulsar.Client") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client

        client = plugin.get_client(mock_container)

        MockClient.assert_called_once_with("pulsar://localhost:6650")
        assert client is mock_client
