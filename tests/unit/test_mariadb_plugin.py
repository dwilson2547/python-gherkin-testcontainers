# tests/unit/test_mariadb_plugin.py
from unittest.mock import patch, MagicMock
from gherkin_testcontainers_mariadb.plugin import MariadbPlugin
from gherkin_testcontainers.plugin import ContainerPlugin


def test_mariadb_plugin_is_a_container_plugin():
    plugin = MariadbPlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_mariadb_plugin_name():
    plugin = MariadbPlugin()
    assert plugin.name == "mariadb"


def test_mariadb_plugin_create_container():
    plugin = MariadbPlugin()
    with patch(
        "gherkin_testcontainers_mariadb.plugin.MySqlContainer"
    ) as MockContainer:
        plugin.create_container(image="mariadb:11")
        MockContainer.assert_called_once_with(image="mariadb:11")
