# tests/unit/test_kafka_plugin.py
from unittest.mock import MagicMock, patch

from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers_kafka.plugin import KafkaPlugin


def test_kafka_plugin_is_a_container_plugin():
    plugin = KafkaPlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_kafka_plugin_name():
    plugin = KafkaPlugin()
    assert plugin.name == "kafka"


def test_kafka_plugin_create_container_returns_kafka_container():
    from testcontainers.kafka import KafkaContainer
    plugin = KafkaPlugin()

    with patch("gherkin_testcontainers_kafka.plugin.KafkaContainer") as MockContainer:
        plugin.create_container(image="confluentinc/cp-kafka:7.6.0")
        MockContainer.assert_called_once_with(image="confluentinc/cp-kafka:7.6.0")


def test_kafka_plugin_create_container_default():
    from testcontainers.kafka import KafkaContainer
    plugin = KafkaPlugin()

    with patch("gherkin_testcontainers_kafka.plugin.KafkaContainer") as MockContainer:
        plugin.create_container()
        MockContainer.assert_called_once_with()


def test_kafka_plugin_get_client_returns_kafka_producer():
    plugin = KafkaPlugin()
    mock_container = MagicMock()
    mock_container.get_bootstrap_server.return_value = "localhost:9093"

    with patch("kafka.KafkaProducer") as MockProducer:
        mock_producer = MagicMock()
        MockProducer.return_value = mock_producer

        client = plugin.get_client(mock_container)

        MockProducer.assert_called_once_with(bootstrap_servers="localhost:9093")
        assert client is mock_producer
