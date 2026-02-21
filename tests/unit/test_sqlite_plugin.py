# tests/unit/test_sqlite_plugin.py
import sqlite3
from gherkin_testcontainers_sqlite.plugin import SqlitePlugin
from gherkin_testcontainers.plugin import ContainerPlugin


def test_sqlite_plugin_is_a_container_plugin():
    plugin = SqlitePlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_sqlite_plugin_name():
    plugin = SqlitePlugin()
    assert plugin.name == "sqlite"


def test_sqlite_plugin_returns_sqlite_connection():
    plugin = SqlitePlugin()
    container = plugin.create_container()
    client = plugin.get_client(container)
    assert isinstance(client, sqlite3.Connection)
    # Verify it works
    client.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
    client.execute("INSERT INTO test VALUES (1)")
    row = client.execute("SELECT id FROM test").fetchone()
    assert row[0] == 1
    client.close()
