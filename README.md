# gherkin-testcontainers

A Python framework that integrates [behave](https://behave.readthedocs.io/) BDD testing with [Testcontainers](https://testcontainers-python.readthedocs.io/). Provides a plugin architecture for any containerized service, step-level decorators for injecting clients, and automatic container lifecycle management scoped to scenarios.

## Installation

```bash
pip install gherkin-testcontainers

# Install plugins for the services you need
pip install gherkin-testcontainers-postgres
pip install gherkin-testcontainers-sqlite
pip install gherkin-testcontainers-mariadb
pip install gherkin-testcontainers-oracle
```

## Quick Start

### 1. Write a feature file

```gherkin
# features/users.feature
Feature: User management

  Scenario: Create and query a user
    Given a fresh database
    When I create a users table
    And I insert a user "Alice"
    Then the users table should contain "Alice"
```

### 2. Wire up behave hooks

```python
# features/environment.py
from gherkin_testcontainers import setup_hooks

setup_hooks(globals())
```

### 3. Write step definitions with `@use_container`

```python
# features/steps/user_steps.py
from behave import given, when, then
from gherkin_testcontainers import use_container

@given("a fresh database")
@use_container("postgres", image="postgres:16")
def step_fresh_db(context, postgres_client):
    context.db = postgres_client

@when("I create a users table")
def step_create_table(context):
    context.db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT)")
    context.db.commit()

@when('I insert a user "{name}"')
def step_insert_user(context, name):
    context.db.execute("INSERT INTO users (name) VALUES (%s)", (name,))
    context.db.commit()

@then('the users table should contain "{name}"')
def step_check_user(context, name):
    row = context.db.execute(
        "SELECT name FROM users WHERE name = %s", (name,)
    ).fetchone()
    assert row is not None
    assert row[0] == name
```

### 4. Run

```bash
behave
```

## How It Works

- **`setup_hooks()`** wires `before_scenario` / `after_scenario` hooks that create and tear down a `ContainerManager` per scenario
- **`@use_container("plugin_name")`** looks up the plugin, starts a container if needed (or reuses an existing one), and injects the raw client as `{plugin_name}_client`
- **Plugins** are auto-discovered via Python entry points — install a plugin package and it's available immediately

## Architecture

```
Your Behave Tests (.feature + steps)
         |
gherkin-testcontainers core
  ├── ContainerManager  (scenario-scoped lifecycle)
  ├── @use_container    (step decorator, client injection)
  └── PluginRegistry    (entry_points auto-discovery)
         |
Plugins (postgres, sqlite, mariadb, oracle, ...)
Each implements ContainerPlugin ABC
         |
testcontainers-python / Docker
```

## Writing a Plugin

Implement the `ContainerPlugin` abstract base class:

```python
from gherkin_testcontainers import ContainerPlugin
from testcontainers.redis import RedisContainer

class RedisPlugin(ContainerPlugin):
    @property
    def name(self) -> str:
        return "redis"

    def create_container(self, **kwargs):
        return RedisContainer(**kwargs)

    def get_client(self, container):
        import redis
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6379)
        return redis.Redis(host=host, port=int(port))
```

Register it in your `pyproject.toml`:

```toml
[project.entry-points."gherkin_testcontainers.plugins"]
redis = "my_package:RedisPlugin"
```

Optional lifecycle hooks are available via `on_start(container)` and `on_stop(container)`.

## Available Plugins

| Plugin | Service | Client |
|--------|---------|--------|
| `gherkin-testcontainers-postgres` | PostgreSQL | `psycopg` connection |
| `gherkin-testcontainers-sqlite` | SQLite (no Docker) | `sqlite3.Connection` |
| `gherkin-testcontainers-mariadb` | MariaDB | SQLAlchemy connection |
| `gherkin-testcontainers-oracle` | Oracle | `oracledb` connection |

## Development

```bash
git clone <repo>
cd gherkin-testcontainers
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install -e plugins/sqlite -e plugins/postgres -e plugins/mariadb --no-deps -e plugins/oracle

# Run tests
pytest tests/unit/ -v
behave tests/integration/features/
```
