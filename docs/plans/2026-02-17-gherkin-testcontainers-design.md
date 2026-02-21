# gherkin-testcontainers Design

## Overview

A Python framework that integrates Gherkin-based BDD testing (via behave) with Testcontainers. Provides a plugin architecture for any containerized service, step-level decorators for injecting clients, and automatic container lifecycle management scoped to scenarios.

Designed to be publishable to PyPI as a core package with independently installable plugin packages.

## Architecture

```
User's Behave Tests (.feature + steps)
         |
gherkin-testcontainers core
  ├── ContainerManager (lifecycle)
  ├── Step Decorators (injection)
  └── PluginRegistry (discovery)
         |
Plugins (postgres, redis, ollama, etc.)
Each implements ContainerPlugin
         |
testcontainers-python / Docker
```

## Core Components

### ContainerPlugin (ABC)

All plugins implement this:

- `name` (property) — Unique plugin name (e.g., "postgres")
- `create_container(**kwargs) -> DockerContainer` — Create and configure the testcontainer
- `get_client(container) -> Any` — Return a raw client/connection from a running container
- `on_start(container)` — Optional hook after container starts
- `on_stop(container)` — Optional hook before container stops

### ContainerManager

Manages container lifecycle per scenario:

- Holds `{plugin_name: (container, client)}` per scenario
- `start(plugin_name, **kwargs)` — Creates container via plugin, starts it, gets client
- `get_client(plugin_name)` — Returns active client, starts container if needed
- `stop_all()` — Tears down all containers, calls `on_stop` hooks

### Step Decorators

`@use_container("plugin_name", **kwargs)` — Wraps a behave step function to:

1. Look up the plugin in the registry
2. Reuse existing container from `context.containers` or start a new one
3. Inject the client as a parameter named `{plugin_name}_client`

### PluginRegistry

Discovers plugins via `entry_points(group="gherkin_testcontainers.plugins")` at import time. Plugins register via `pyproject.toml`:

```toml
[project.entry-points."gherkin_testcontainers.plugins"]
postgres = "gherkin_testcontainers_postgres:PostgresPlugin"
```

### Behave Integration

Quick setup via `setup_hooks(globals())` or manual wiring in `environment.py`:

```python
from gherkin_testcontainers import ContainerManager

def before_scenario(context, scenario):
    context.containers = ContainerManager()

def after_scenario(context, scenario):
    context.containers.stop_all()
```

## Project Structure

Monorepo with independently installable packages:

```
gherkin-testcontainers/
├── pyproject.toml                          # Core package
├── src/gherkin_testcontainers/
│   ├── __init__.py
│   ├── plugin.py                           # ContainerPlugin ABC
│   ├── manager.py                          # ContainerManager
│   ├── decorators.py                       # @use_container
│   ├── registry.py                         # PluginRegistry
│   └── hooks.py                            # Behave environment integration
├── plugins/
│   ├── postgres/pyproject.toml + src/...   # PostgresPlugin
│   ├── sqlite/...                          # SqlitePlugin
│   ├── mariadb/...                         # MariadbPlugin
│   └── oracle/...                          # OraclePlugin
├── tests/
│   ├── features/                           # .feature files
│   ├── steps/                              # Step definitions
│   └── environment.py
└── docs/plans/
```

## Dependencies

- **Core:** `testcontainers`, `behave`
- **Plugins:** Core + service-specific client library (e.g., `psycopg` for postgres)

## Usage Example

```python
from behave import given, when, then
from gherkin_testcontainers import use_container

@given('a database with users')
@use_container("postgres", image="postgres:16", env={"POSTGRES_PASSWORD": "test"})
def step_given_db(context, postgres_client):
    postgres_client.execute("CREATE TABLE users ...")

@when('I query the LLM with "{prompt}"')
@use_container("ollama", model="llama3")
def step_query_llm(context, ollama_client, prompt):
    context.response = ollama_client.generate(prompt)
```

## Design Decisions

- **Raw client injection** — Plugins return native clients, not wrappers. Domain-layer abstractions can be added later.
- **Scenario-scoped containers** — Fresh containers per scenario for test isolation.
- **Entry-point discovery** — Standard Python packaging pattern for auto-discovery.
- **Monorepo** — All plugins in one repo for development convenience, each independently installable.
