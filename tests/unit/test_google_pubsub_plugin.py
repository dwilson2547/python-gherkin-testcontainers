# tests/unit/test_google_pubsub_plugin.py
from unittest.mock import patch, MagicMock
from gherkin_testcontainers_google_pubsub.plugin import GooglePubSubPlugin
from gherkin_testcontainers.plugin import ContainerPlugin


def test_google_pubsub_plugin_is_a_container_plugin():
    plugin = GooglePubSubPlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_google_pubsub_plugin_name():
    plugin = GooglePubSubPlugin()
    assert plugin.name == "google_pubsub"


def test_google_pubsub_plugin_create_container():
    plugin = GooglePubSubPlugin()
    with patch(
        "gherkin_testcontainers_google_pubsub.plugin.PubSubContainer"
    ) as MockContainer:
        plugin.create_container(project="test-project")
        MockContainer.assert_called_once_with(project="test-project")
