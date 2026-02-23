# tests/unit/test_eventhubs_plugin.py
from unittest.mock import MagicMock, patch

from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers_eventhubs.plugin import (
    DEFAULT_EVENTHUBS_IMAGE,
    DEFAULT_EVENTHUB_NAME,
    DEFAULT_EVENTHUB_NAMESPACE,
    EVENTHUBS_AMQP_PORT,
    EVENTHUBS_SHARED_ACCESS_KEY,
    EVENTHUBS_SHARED_ACCESS_KEY_NAME,
    EventHubsContainer,
    EventHubsPlugin,
)


def test_eventhubs_plugin_is_a_container_plugin():
    plugin = EventHubsPlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_eventhubs_plugin_name():
    plugin = EventHubsPlugin()
    assert plugin.name == "eventhubs"


def test_eventhubs_plugin_create_container_returns_eventhubs_container():
    plugin = EventHubsPlugin()
    container = plugin.create_container()
    assert isinstance(container, EventHubsContainer)


def test_eventhubs_plugin_create_container_custom_image():
    plugin = EventHubsPlugin()

    with patch("gherkin_testcontainers_eventhubs.plugin.EventHubsContainer") as MockContainer:
        plugin.create_container(image="mcr.microsoft.com/azure-messaging/eventhubs-emulator:1.0.0")
        MockContainer.assert_called_once_with(image="mcr.microsoft.com/azure-messaging/eventhubs-emulator:1.0.0")


def test_eventhubs_container_default_image():
    assert DEFAULT_EVENTHUBS_IMAGE == "mcr.microsoft.com/azure-messaging/eventhubs-emulator:latest"


def test_eventhubs_container_constants():
    assert EVENTHUBS_AMQP_PORT == 5672
    assert DEFAULT_EVENTHUB_NAMESPACE == "emulatorNs1"
    assert DEFAULT_EVENTHUB_NAME == "eh1"
    assert EVENTHUBS_SHARED_ACCESS_KEY_NAME == "RootManageSharedAccessKey"
    assert EVENTHUBS_SHARED_ACCESS_KEY == "SAS_KEY_VALUE"


def test_eventhubs_container_get_connection_string_default():
    container = MagicMock(spec=EventHubsContainer)
    container.get_container_host_ip.return_value = "localhost"
    container.get_exposed_port.return_value = "15672"
    container.get_connection_string = EventHubsContainer.get_connection_string.__get__(container)

    conn_str = container.get_connection_string()

    container.get_exposed_port.assert_called_once_with(EVENTHUBS_AMQP_PORT)
    assert "Endpoint=sb://localhost:15672;" in conn_str
    assert f"SharedAccessKeyName={EVENTHUBS_SHARED_ACCESS_KEY_NAME};" in conn_str
    assert f"SharedAccessKey={EVENTHUBS_SHARED_ACCESS_KEY};" in conn_str
    assert f"EntityPath={DEFAULT_EVENTHUB_NAME};" in conn_str
    assert "UseDevelopmentEmulator=true;" in conn_str


def test_eventhubs_container_get_connection_string_custom_eventhub():
    container = MagicMock(spec=EventHubsContainer)
    container.get_container_host_ip.return_value = "localhost"
    container.get_exposed_port.return_value = "15672"
    container.get_connection_string = EventHubsContainer.get_connection_string.__get__(container)

    conn_str = container.get_connection_string(eventhub_name="my-hub")

    assert "EntityPath=my-hub;" in conn_str


def test_eventhubs_plugin_get_client_returns_producer():
    plugin = EventHubsPlugin()
    mock_container = MagicMock(spec=EventHubsContainer)
    mock_container.get_connection_string.return_value = (
        "Endpoint=sb://localhost:15672;"
        "SharedAccessKeyName=RootManageSharedAccessKey;"
        "SharedAccessKey=SAS_KEY_VALUE;"
        "EntityPath=eh1;"
        "UseDevelopmentEmulator=true;"
    )

    with patch("azure.eventhub.EventHubProducerClient.from_connection_string") as MockProducer:
        mock_producer = MagicMock()
        MockProducer.return_value = mock_producer

        client = plugin.get_client(mock_container)

        MockProducer.assert_called_once_with(mock_container.get_connection_string.return_value)
        assert client is mock_producer
