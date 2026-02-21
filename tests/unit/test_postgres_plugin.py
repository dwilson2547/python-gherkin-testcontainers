# tests/unit/test_postgres_plugin.py
from gherkin_testcontainers_postgres.plugin import PostgresPlugin
from gherkin_testcontainers.plugin import ContainerPlugin


def test_postgres_plugin_is_a_container_plugin():
    plugin = PostgresPlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_postgres_plugin_name():
    plugin = PostgresPlugin()
    assert plugin.name == "postgres"


def test_postgres_plugin_create_container_returns_postgres_container():
    from unittest.mock import patch, MagicMock
    plugin = PostgresPlugin()

    with patch(
        "gherkin_testcontainers_postgres.plugin.PostgresContainer"
    ) as MockContainer:
        container = plugin.create_container(
            image="postgres:16",
            username="test",
            password="test",
            dbname="testdb",
        )
        MockContainer.assert_called_once_with(
            image="postgres:16",
            username="test",
            password="test",
            dbname="testdb",
        )
