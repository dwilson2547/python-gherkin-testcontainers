# tests/unit/test_iggy_plugin.py
from unittest.mock import patch, MagicMock
from gherkin_testcontainers_iggy.plugin import (
    IggyPlugin,
    DEFAULT_IGGY_IMAGE,
    IGGY_HTTP_PORT,
    IGGY_TCP_PORT,
)
from gherkin_testcontainers.plugin import ContainerPlugin


def test_iggy_plugin_is_a_container_plugin():
    plugin = IggyPlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_iggy_plugin_name():
    plugin = IggyPlugin()
    assert plugin.name == "iggy"


def test_iggy_plugin_create_container_default_image():
    plugin = IggyPlugin()
    with patch(
        "gherkin_testcontainers_iggy.plugin.DockerContainer"
    ) as MockContainer:
        mock_instance = MagicMock()
        MockContainer.return_value = mock_instance
        container = plugin.create_container()
        MockContainer.assert_called_once_with(DEFAULT_IGGY_IMAGE)
        mock_instance.with_exposed_ports.assert_called_once_with(
            IGGY_HTTP_PORT, IGGY_TCP_PORT
        )


def test_iggy_plugin_create_container_custom_image():
    plugin = IggyPlugin()
    with patch(
        "gherkin_testcontainers_iggy.plugin.DockerContainer"
    ) as MockContainer:
        mock_instance = MagicMock()
        MockContainer.return_value = mock_instance
        container = plugin.create_container(image="iggyrs/iggy:0.4.21")
        MockContainer.assert_called_once_with("iggyrs/iggy:0.4.21")
        mock_instance.with_exposed_ports.assert_called_once_with(
            IGGY_HTTP_PORT, IGGY_TCP_PORT
        )


def test_iggy_plugin_get_client_returns_iggy_client():
    plugin = IggyPlugin()
    mock_container = MagicMock()
    mock_container.get_container_host_ip.return_value = "localhost"
    mock_container.get_exposed_port.return_value = "12345"

    with patch("iggy_py.IggyClient") as MockIggyClient:
        mock_client = MagicMock()
        MockIggyClient.return_value = mock_client

        client = plugin.get_client(mock_container)

        mock_container.get_container_host_ip.assert_called_once()
        mock_container.get_exposed_port.assert_called_once_with(IGGY_TCP_PORT)
        MockIggyClient.assert_called_once_with(host="localhost", port=12345)
        assert client is mock_client
