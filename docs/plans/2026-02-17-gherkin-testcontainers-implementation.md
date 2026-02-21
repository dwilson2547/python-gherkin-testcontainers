# gherkin-testcontainers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python framework that integrates behave BDD testing with Testcontainers, providing a plugin architecture for any containerized service with step-level decorators for client injection.

**Architecture:** Core package defines a ContainerPlugin ABC, a PluginRegistry for entry_point-based discovery, a ContainerManager for scenario-scoped container lifecycle, and a `@use_container` decorator for injecting raw clients into behave step functions. Plugins are separate packages that implement ContainerPlugin for specific services.

**Tech Stack:** Python 3.11+, behave, testcontainers-python, hatchling (build backend), pytest (for unit tests of the framework itself)

---

### Task 1: Scaffold core package

**Files:**
- Create: `pyproject.toml`
- Create: `src/gherkin_testcontainers/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gherkin-testcontainers"
version = "0.1.0"
description = "BDD testing framework integrating behave with testcontainers"
requires-python = ">=3.11"
dependencies = [
    "behave>=1.2.6",
    "testcontainers>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-mock>=3.0",
]
```

**Step 2: Create package init**

```python
# src/gherkin_testcontainers/__init__.py
```

Empty for now — we'll add public exports as we build each module.

**Step 3: Create virtual environment and install**

Run: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: Package installs successfully with behave, testcontainers, pytest.

**Step 4: Commit**

```
feat: scaffold core package with pyproject.toml
```

---

### Task 2: Implement ContainerPlugin ABC

**Files:**
- Create: `src/gherkin_testcontainers/plugin.py`
- Create: `tests/unit/test_plugin.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_plugin.py
from gherkin_testcontainers.plugin import ContainerPlugin


def test_cannot_instantiate_abstract_plugin():
    """ContainerPlugin is abstract and cannot be instantiated directly."""
    import pytest
    with pytest.raises(TypeError):
        ContainerPlugin()


def test_concrete_plugin_must_implement_required_methods():
    """A subclass that doesn't implement abstract methods cannot be instantiated."""
    import pytest

    class IncompletePlugin(ContainerPlugin):
        pass

    with pytest.raises(TypeError):
        IncompletePlugin()


def test_concrete_plugin_can_be_instantiated():
    """A subclass implementing all abstract methods can be instantiated."""
    from unittest.mock import MagicMock

    class FakePlugin(ContainerPlugin):
        @property
        def name(self) -> str:
            return "fake"

        def create_container(self, **kwargs):
            return MagicMock()

        def get_client(self, container):
            return MagicMock()

    plugin = FakePlugin()
    assert plugin.name == "fake"


def test_on_start_and_on_stop_are_optional_noops():
    """Default on_start and on_stop do nothing and don't raise."""
    from unittest.mock import MagicMock

    class FakePlugin(ContainerPlugin):
        @property
        def name(self) -> str:
            return "fake"

        def create_container(self, **kwargs):
            return MagicMock()

        def get_client(self, container):
            return MagicMock()

    plugin = FakePlugin()
    container = MagicMock()
    plugin.on_start(container)  # should not raise
    plugin.on_stop(container)   # should not raise
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_plugin.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gherkin_testcontainers.plugin'`

**Step 3: Write minimal implementation**

```python
# src/gherkin_testcontainers/plugin.py
from abc import ABC, abstractmethod
from typing import Any

from testcontainers.core.container import DockerContainer


class ContainerPlugin(ABC):
    """Base class for all container plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier, e.g. 'postgres'."""

    @abstractmethod
    def create_container(self, **kwargs) -> DockerContainer:
        """Create and configure a testcontainer instance."""

    @abstractmethod
    def get_client(self, container: DockerContainer) -> Any:
        """Return a raw client/connection from a running container."""

    def on_start(self, container: DockerContainer) -> None:
        """Optional hook called after container starts."""

    def on_stop(self, container: DockerContainer) -> None:
        """Optional hook called before container stops."""
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_plugin.py -v`
Expected: All 4 tests PASS.

**Step 5: Commit**

```
feat: add ContainerPlugin abstract base class
```

---

### Task 3: Implement PluginRegistry

**Files:**
- Create: `src/gherkin_testcontainers/registry.py`
- Create: `tests/unit/test_registry.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_registry.py
import pytest
from unittest.mock import MagicMock, patch
from gherkin_testcontainers.registry import PluginRegistry
from gherkin_testcontainers.plugin import ContainerPlugin


class FakePlugin(ContainerPlugin):
    @property
    def name(self) -> str:
        return "fake"

    def create_container(self, **kwargs):
        return MagicMock()

    def get_client(self, container):
        return MagicMock()


@pytest.fixture(autouse=True)
def clean_registry():
    """Reset registry state between tests."""
    PluginRegistry._plugins.clear()
    yield
    PluginRegistry._plugins.clear()


def test_register_and_get_plugin():
    PluginRegistry.register("fake", FakePlugin)
    plugin = PluginRegistry.get("fake")
    assert isinstance(plugin, FakePlugin)
    assert plugin.name == "fake"


def test_get_unknown_plugin_raises():
    with pytest.raises(KeyError, match="no_such_plugin"):
        PluginRegistry.get("no_such_plugin")


def test_discover_loads_entry_points():
    mock_ep = MagicMock()
    mock_ep.name = "fake"
    mock_ep.load.return_value = FakePlugin

    with patch(
        "gherkin_testcontainers.registry.entry_points",
        return_value=[mock_ep],
    ):
        PluginRegistry.discover()

    plugin = PluginRegistry.get("fake")
    assert isinstance(plugin, FakePlugin)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/gherkin_testcontainers/registry.py
from importlib.metadata import entry_points

from gherkin_testcontainers.plugin import ContainerPlugin


class PluginRegistry:
    """Discovers and stores container plugins."""

    _plugins: dict[str, type[ContainerPlugin]] = {}

    @classmethod
    def register(cls, name: str, plugin_class: type[ContainerPlugin]) -> None:
        cls._plugins[name] = plugin_class

    @classmethod
    def get(cls, name: str) -> ContainerPlugin:
        if name not in cls._plugins:
            raise KeyError(
                f"Plugin '{name}' not found. "
                f"Available: {list(cls._plugins.keys())}"
            )
        return cls._plugins[name]()

    @classmethod
    def discover(cls) -> None:
        for ep in entry_points(group="gherkin_testcontainers.plugins"):
            cls._plugins[ep.name] = ep.load()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_registry.py -v`
Expected: All 3 tests PASS.

**Step 5: Commit**

```
feat: add PluginRegistry with entry_points discovery
```

---

### Task 4: Implement ContainerManager

**Files:**
- Create: `src/gherkin_testcontainers/manager.py`
- Create: `tests/unit/test_manager.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_manager.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/gherkin_testcontainers/manager.py
from typing import Any

from testcontainers.core.container import DockerContainer

from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers.registry import PluginRegistry


class ContainerManager:
    """Manages container lifecycle for a single scenario."""

    def __init__(self) -> None:
        self._containers: dict[str, tuple[DockerContainer, Any]] = {}

    def start(self, plugin_name: str, **kwargs) -> Any:
        if plugin_name in self._containers:
            _, client = self._containers[plugin_name]
            return client

        plugin = PluginRegistry.get(plugin_name)
        container = plugin.create_container(**kwargs)
        container.start()
        plugin.on_start(container)
        client = plugin.get_client(container)
        self._containers[plugin_name] = (container, client)
        return client

    def get_client(self, plugin_name: str, **kwargs) -> Any:
        if plugin_name in self._containers:
            _, client = self._containers[plugin_name]
            return client
        return self.start(plugin_name, **kwargs)

    def stop_all(self) -> None:
        for plugin_name, (container, _) in self._containers.items():
            plugin = PluginRegistry.get(plugin_name)
            plugin.on_stop(container)
            container.stop()
        self._containers.clear()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_manager.py -v`
Expected: All 6 tests PASS.

**Step 5: Commit**

```
feat: add ContainerManager for scenario-scoped lifecycle
```

---

### Task 5: Implement @use_container decorator

**Files:**
- Create: `src/gherkin_testcontainers/decorators.py`
- Create: `tests/unit/test_decorators.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_decorators.py
import pytest
from unittest.mock import MagicMock, patch
from gherkin_testcontainers.decorators import use_container
from gherkin_testcontainers.manager import ContainerManager
from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers.registry import PluginRegistry


class FakePlugin(ContainerPlugin):
    @property
    def name(self) -> str:
        return "fake"

    def create_container(self, **kwargs):
        return MagicMock()

    def get_client(self, container):
        return MagicMock(name="fake_client")


@pytest.fixture(autouse=True)
def clean_registry():
    PluginRegistry._plugins.clear()
    PluginRegistry.register("fake", FakePlugin)
    yield
    PluginRegistry._plugins.clear()


def _make_context():
    context = MagicMock()
    context.containers = ContainerManager()
    return context


def test_decorator_injects_client_as_named_param():
    @use_container("fake")
    def step_fn(context, fake_client):
        return fake_client

    ctx = _make_context()
    result = step_fn(ctx)
    assert result is not None


def test_decorator_preserves_other_params():
    @use_container("fake")
    def step_fn(context, fake_client, name):
        return f"{name}:{fake_client}"

    ctx = _make_context()
    result = step_fn(ctx, name="test")
    assert "test:" in str(result)


def test_decorator_passes_kwargs_to_container():
    @use_container("fake", image="custom:1")
    def step_fn(context, fake_client):
        return fake_client

    ctx = _make_context()
    step_fn(ctx)
    # Container was started — client exists
    assert ctx.containers.get_client("fake") is not None


def test_decorator_reuses_existing_container():
    ctx = _make_context()
    client1 = ctx.containers.start("fake")

    @use_container("fake")
    def step_fn(context, fake_client):
        return fake_client

    client2 = step_fn(ctx)
    assert client1 is client2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_decorators.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/gherkin_testcontainers/decorators.py
import functools
from typing import Any, Callable


def use_container(plugin_name: str, **container_kwargs) -> Callable:
    """Decorator that injects a container client into a behave step function.

    The client is injected as a keyword argument named '{plugin_name}_client'.
    """
    client_param = f"{plugin_name}_client"

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(context, *args, **kwargs):
            client = context.containers.get_client(
                plugin_name, **container_kwargs
            )
            kwargs[client_param] = client
            return fn(context, *args, **kwargs)

        return wrapper

    return decorator
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_decorators.py -v`
Expected: All 4 tests PASS.

**Step 5: Commit**

```
feat: add @use_container step decorator
```

---

### Task 6: Implement behave hooks integration

**Files:**
- Create: `src/gherkin_testcontainers/hooks.py`
- Create: `tests/unit/test_hooks.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_hooks.py
from unittest.mock import MagicMock, patch
from gherkin_testcontainers.hooks import setup_hooks
from gherkin_testcontainers.manager import ContainerManager


def test_setup_hooks_adds_before_and_after_scenario():
    namespace = {}
    setup_hooks(namespace)
    assert "before_scenario" in namespace
    assert "after_scenario" in namespace


def test_before_scenario_creates_container_manager():
    namespace = {}
    setup_hooks(namespace)
    context = MagicMock()
    scenario = MagicMock()
    namespace["before_scenario"](context, scenario)
    assert isinstance(context.containers, ContainerManager)


def test_after_scenario_calls_stop_all():
    namespace = {}
    setup_hooks(namespace)
    context = MagicMock()
    scenario = MagicMock()

    # Simulate before + after
    namespace["before_scenario"](context, scenario)
    manager = context.containers
    with patch.object(manager, "stop_all") as mock_stop:
        namespace["after_scenario"](context, scenario)
        mock_stop.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_hooks.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/gherkin_testcontainers/hooks.py
from gherkin_testcontainers.manager import ContainerManager


def setup_hooks(namespace: dict) -> None:
    """Wire behave lifecycle hooks into the given namespace (environment.py globals)."""

    def before_scenario(context, scenario):
        context.containers = ContainerManager()

    def after_scenario(context, scenario):
        context.containers.stop_all()

    namespace["before_scenario"] = before_scenario
    namespace["after_scenario"] = after_scenario
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_hooks.py -v`
Expected: All 3 tests PASS.

**Step 5: Commit**

```
feat: add behave hooks integration via setup_hooks()
```

---

### Task 7: Wire up public API exports

**Files:**
- Modify: `src/gherkin_testcontainers/__init__.py`
- Create: `tests/unit/test_public_api.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_public_api.py
def test_public_api_imports():
    from gherkin_testcontainers import (
        ContainerPlugin,
        ContainerManager,
        PluginRegistry,
        use_container,
        setup_hooks,
    )
    assert ContainerPlugin is not None
    assert ContainerManager is not None
    assert PluginRegistry is not None
    assert use_container is not None
    assert setup_hooks is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_public_api.py -v`
Expected: FAIL — `ImportError`

**Step 3: Write implementation**

```python
# src/gherkin_testcontainers/__init__.py
from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers.registry import PluginRegistry
from gherkin_testcontainers.manager import ContainerManager
from gherkin_testcontainers.decorators import use_container
from gherkin_testcontainers.hooks import setup_hooks

__all__ = [
    "ContainerPlugin",
    "PluginRegistry",
    "ContainerManager",
    "use_container",
    "setup_hooks",
]

# Auto-discover installed plugins
PluginRegistry.discover()
```

**Step 4: Run all tests**

Run: `pytest tests/unit/ -v`
Expected: All tests PASS.

**Step 5: Commit**

```
feat: wire up public API exports with auto-discovery
```

---

### Task 8: Implement Postgres plugin

**Files:**
- Create: `plugins/postgres/pyproject.toml`
- Create: `plugins/postgres/src/gherkin_testcontainers_postgres/__init__.py`
- Create: `plugins/postgres/src/gherkin_testcontainers_postgres/plugin.py`
- Create: `tests/unit/test_postgres_plugin.py`

**Step 1: Create plugin pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gherkin-testcontainers-postgres"
version = "0.1.0"
description = "PostgreSQL plugin for gherkin-testcontainers"
requires-python = ">=3.11"
dependencies = [
    "gherkin-testcontainers>=0.1.0",
    "testcontainers[postgres]>=4.0.0",
    "psycopg>=3.0",
]

[project.entry-points."gherkin_testcontainers.plugins"]
postgres = "gherkin_testcontainers_postgres:PostgresPlugin"
```

**Step 2: Write the failing test**

```python
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
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_postgres_plugin.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write implementation**

```python
# plugins/postgres/src/gherkin_testcontainers_postgres/__init__.py
from gherkin_testcontainers_postgres.plugin import PostgresPlugin

__all__ = ["PostgresPlugin"]
```

```python
# plugins/postgres/src/gherkin_testcontainers_postgres/plugin.py
from typing import Any

from testcontainers.postgres import PostgresContainer

from gherkin_testcontainers.plugin import ContainerPlugin


class PostgresPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "postgres"

    def create_container(self, **kwargs) -> PostgresContainer:
        return PostgresContainer(**kwargs)

    def get_client(self, container: PostgresContainer) -> Any:
        import psycopg
        url = container.get_connection_url()
        return psycopg.connect(url)
```

**Step 5: Install plugin in dev mode and run tests**

Run: `pip install -e plugins/postgres && pytest tests/unit/test_postgres_plugin.py -v`
Expected: All 3 tests PASS.

**Step 6: Commit**

```
feat: add postgres plugin
```

---

### Task 9: Implement SQLite plugin

**Files:**
- Create: `plugins/sqlite/pyproject.toml`
- Create: `plugins/sqlite/src/gherkin_testcontainers_sqlite/__init__.py`
- Create: `plugins/sqlite/src/gherkin_testcontainers_sqlite/plugin.py`
- Create: `tests/unit/test_sqlite_plugin.py`

**Note:** SQLite doesn't need a container — it's an in-process database. This plugin demonstrates that the plugin architecture isn't limited to Docker containers. It uses a temp file and returns a standard `sqlite3.Connection`.

**Step 1: Create plugin pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gherkin-testcontainers-sqlite"
version = "0.1.0"
description = "SQLite plugin for gherkin-testcontainers"
requires-python = ">=3.11"
dependencies = [
    "gherkin-testcontainers>=0.1.0",
]

[project.entry-points."gherkin_testcontainers.plugins"]
sqlite = "gherkin_testcontainers_sqlite:SqlitePlugin"
```

**Step 2: Write the failing test**

```python
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
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_sqlite_plugin.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write implementation**

```python
# plugins/sqlite/src/gherkin_testcontainers_sqlite/__init__.py
from gherkin_testcontainers_sqlite.plugin import SqlitePlugin

__all__ = ["SqlitePlugin"]
```

```python
# plugins/sqlite/src/gherkin_testcontainers_sqlite/plugin.py
import sqlite3
import tempfile
from dataclasses import dataclass, field
from typing import Any

from gherkin_testcontainers.plugin import ContainerPlugin


@dataclass
class SqliteContainer:
    """Lightweight stand-in for a DockerContainer — just holds a temp file path."""
    db_path: str = field(default="")

    def start(self):
        if not self.db_path:
            self.db_path = tempfile.mktemp(suffix=".db")
        return self

    def stop(self):
        import os
        if self.db_path and os.path.exists(self.db_path):
            os.remove(self.db_path)


class SqlitePlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "sqlite"

    def create_container(self, **kwargs) -> SqliteContainer:
        return SqliteContainer(**kwargs)

    def get_client(self, container: SqliteContainer) -> Any:
        return sqlite3.connect(container.db_path)
```

**Step 5: Install and run tests**

Run: `pip install -e plugins/sqlite && pytest tests/unit/test_sqlite_plugin.py -v`
Expected: All 3 tests PASS.

**Step 6: Commit**

```
feat: add sqlite plugin
```

---

### Task 10: Implement MariaDB plugin

**Files:**
- Create: `plugins/mariadb/pyproject.toml`
- Create: `plugins/mariadb/src/gherkin_testcontainers_mariadb/__init__.py`
- Create: `plugins/mariadb/src/gherkin_testcontainers_mariadb/plugin.py`
- Create: `tests/unit/test_mariadb_plugin.py`

**Step 1: Create plugin pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gherkin-testcontainers-mariadb"
version = "0.1.0"
description = "MariaDB plugin for gherkin-testcontainers"
requires-python = ">=3.11"
dependencies = [
    "gherkin-testcontainers>=0.1.0",
    "testcontainers>=4.0.0",
    "mariadb>=1.1.0",
]

[project.entry-points."gherkin_testcontainers.plugins"]
mariadb = "gherkin_testcontainers_mariadb:MariadbPlugin"
```

**Step 2: Write the failing test**

```python
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
        "gherkin_testcontainers_mariadb.plugin.MariaDbContainer"
    ) as MockContainer:
        plugin.create_container(image="mariadb:11")
        MockContainer.assert_called_once_with(image="mariadb:11")
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_mariadb_plugin.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write implementation**

```python
# plugins/mariadb/src/gherkin_testcontainers_mariadb/__init__.py
from gherkin_testcontainers_mariadb.plugin import MariadbPlugin

__all__ = ["MariadbPlugin"]
```

```python
# plugins/mariadb/src/gherkin_testcontainers_mariadb/plugin.py
from typing import Any

from testcontainers.mariadb import MariaDbContainer

from gherkin_testcontainers.plugin import ContainerPlugin


class MariadbPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "mariadb"

    def create_container(self, **kwargs) -> MariaDbContainer:
        return MariaDbContainer(**kwargs)

    def get_client(self, container: MariaDbContainer) -> Any:
        import mariadb
        connection_params = {
            "host": container.get_container_host_ip(),
            "port": int(container.get_exposed_port(3306)),
            "user": container.username,
            "password": container.password,
            "database": container.dbname,
        }
        return mariadb.connect(**connection_params)
```

**Step 5: Install and run tests**

Run: `pip install -e plugins/mariadb && pytest tests/unit/test_mariadb_plugin.py -v`
Expected: All 3 tests PASS.

**Step 6: Commit**

```
feat: add mariadb plugin
```

---

### Task 11: Implement Oracle plugin

**Files:**
- Create: `plugins/oracle/pyproject.toml`
- Create: `plugins/oracle/src/gherkin_testcontainers_oracle/__init__.py`
- Create: `plugins/oracle/src/gherkin_testcontainers_oracle/plugin.py`
- Create: `tests/unit/test_oracle_plugin.py`

**Step 1: Create plugin pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gherkin-testcontainers-oracle"
version = "0.1.0"
description = "Oracle plugin for gherkin-testcontainers"
requires-python = ">=3.11"
dependencies = [
    "gherkin-testcontainers>=0.1.0",
    "testcontainers[oracle-free]>=4.0.0",
    "oracledb>=2.0",
]

[project.entry-points."gherkin_testcontainers.plugins"]
oracle = "gherkin_testcontainers_oracle:OraclePlugin"
```

**Step 2: Write the failing test**

```python
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
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_oracle_plugin.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write implementation**

```python
# plugins/oracle/src/gherkin_testcontainers_oracle/__init__.py
from gherkin_testcontainers_oracle.plugin import OraclePlugin

__all__ = ["OraclePlugin"]
```

```python
# plugins/oracle/src/gherkin_testcontainers_oracle/plugin.py
from typing import Any

from testcontainers.oracle import OracleDbContainer

from gherkin_testcontainers.plugin import ContainerPlugin


class OraclePlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "oracle"

    def create_container(self, **kwargs) -> OracleDbContainer:
        return OracleDbContainer(**kwargs)

    def get_client(self, container: OracleDbContainer) -> Any:
        import oracledb
        return oracledb.connect(
            user=container.username,
            password=container.password,
            dsn=f"{container.get_container_host_ip()}:{container.get_exposed_port(1521)}/{container.dbname}",
        )
```

**Step 5: Install and run tests**

Run: `pip install -e plugins/oracle && pytest tests/unit/test_oracle_plugin.py -v`
Expected: All 3 tests PASS.

**Step 6: Commit**

```
feat: add oracle plugin
```

---

### Task 12: End-to-end integration test with behave + SQLite

**Files:**
- Create: `tests/integration/features/sqlite_crud.feature`
- Create: `tests/integration/features/steps/sqlite_steps.py`
- Create: `tests/integration/features/environment.py`

**Why SQLite:** It requires no Docker daemon, so this integration test runs anywhere. Docker-based integration tests (postgres, mariadb, oracle) can be run manually or in CI with Docker available.

**Step 1: Write the feature file**

```gherkin
# tests/integration/features/sqlite_crud.feature
Feature: SQLite CRUD operations

  Scenario: Create a table and insert a record
    Given a fresh SQLite database
    When I create a users table
    And I insert a user "Alice"
    Then the users table should contain "Alice"
```

**Step 2: Write the environment.py**

```python
# tests/integration/features/environment.py
from gherkin_testcontainers import setup_hooks

setup_hooks(globals())
```

**Step 3: Write the step definitions**

```python
# tests/integration/features/steps/sqlite_steps.py
from behave import given, when, then
from gherkin_testcontainers import use_container


@given("a fresh SQLite database")
@use_container("sqlite")
def step_fresh_db(context, sqlite_client):
    context.db = sqlite_client


@when("I create a users table")
def step_create_table(context):
    context.db.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    )
    context.db.commit()


@when('I insert a user "{name}"')
def step_insert_user(context, name):
    context.db.execute("INSERT INTO users (name) VALUES (?)", (name,))
    context.db.commit()


@then('the users table should contain "{name}"')
def step_check_user(context, name):
    row = context.db.execute(
        "SELECT name FROM users WHERE name = ?", (name,)
    ).fetchone()
    assert row is not None, f"User '{name}' not found"
    assert row[0] == name
```

**Step 4: Run the integration test**

Run: `behave tests/integration/features/sqlite_crud.feature`
Expected: 1 scenario passed, 4 steps passed.

**Step 5: Commit**

```
test: add end-to-end integration test with behave + sqlite
```

---

### Task 13: Run full test suite and verify

**Step 1: Run all unit tests**

Run: `pytest tests/unit/ -v`
Expected: All tests PASS.

**Step 2: Run integration test**

Run: `behave tests/integration/features/`
Expected: All scenarios PASS.

**Step 3: Final commit**

```
chore: verify full test suite passes
```
