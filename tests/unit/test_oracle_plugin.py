# tests/unit/test_oracle_plugin.py
from unittest.mock import patch, MagicMock
from gherkin_testcontainers_oracle.plugin import OraclePlugin
from gherkin_testcontainers.plugin import ContainerPlugin


def test_oracle_plugin_is_a_container_plugin():
    plugin = OraclePlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_oracle_plugin_name():
    plugin = OraclePlugin()
    assert plugin.name == "oracle"


def test_oracle_plugin_create_container():
    plugin = OraclePlugin()
    with patch(
        "gherkin_testcontainers_oracle.plugin.OracleDbContainer"
    ) as MockContainer:
        plugin.create_container(image="gvenzl/oracle-free:slim")
        MockContainer.assert_called_once_with(image="gvenzl/oracle-free:slim")
