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
pip install gherkin-testcontainers-playwright
pip install gherkin-testcontainers-kafka
pip install gherkin-testcontainers-pulsar
pip install gherkin-testcontainers-eventhubs
pip install gherkin-testcontainers-google-pubsub
pip install gherkin-testcontainers-iggy
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
Plugins (postgres, sqlite, mariadb, oracle, kafka, pulsar, eventhubs, ...)
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
| `gherkin-testcontainers-playwright` | Playwright browser (no Docker) | `playwright.sync_api.Page` |
| `gherkin-testcontainers-kafka` | Apache Kafka | `kafka.KafkaProducer` |
| `gherkin-testcontainers-pulsar` | Apache Pulsar | `pulsar.Client` |
| `gherkin-testcontainers-eventhubs` | Azure Event Hubs (emulator) | `azure.eventhub.EventHubProducerClient` |
| `gherkin-testcontainers-google-pubsub` | Google Cloud Pub/Sub emulator | `google.cloud.pubsub_v1.PublisherClient` |
| `gherkin-testcontainers-iggy` | Iggy message streaming | `iggy_py.IggyClient` |

## Playwright Integration

The `playwright` plugin lets you drive a real browser inside BDD scenarios. It does not require Docker — it manages a [Playwright](https://playwright.dev/python/) browser instance directly. Combine it with other container plugins to spin up a backend or UI container, then use Playwright to test flows through the site.

### Installation

```bash
pip install gherkin-testcontainers-playwright
playwright install  # downloads browser binaries
```

### Example

```gherkin
# features/ui.feature
Feature: UI smoke test

  Scenario: Home page loads
    Given a running web app
    When I open the home page
    Then I should see the title "My App"
```

```python
# features/steps/ui_steps.py
from behave import given, when, then
from gherkin_testcontainers import use_container

@given("a running web app")
@use_container("playwright", browser_type="chromium", headless=True)
def step_running_app(context, playwright_client):
    # playwright_client is a playwright.sync_api.Page
    context.page = playwright_client

@when("I open the home page")
def step_open_home(context):
    context.page.goto("http://localhost:8080")

@then('I should see the title "{title}"')
def step_check_title(context, title):
    assert context.page.title() == title
```

Supported `@use_container` kwargs:

| Kwarg | Default | Description |
|-------|---------|-------------|
| `browser_type` | `"chromium"` | Browser to launch: `"chromium"`, `"firefox"`, or `"webkit"` |
| `headless` | `True` | Run headlessly (no visible window) |
| `slow_mo` | — | Milliseconds to slow each operation (useful for debugging) |
| any other kwarg | — | Forwarded directly to `browser.launch()` |

## Kafka Integration

The `kafka` plugin spins up a [Confluent Kafka](https://hub.docker.com/r/confluentinc/cp-kafka) container and injects a `kafka.KafkaProducer` client. Use the producer to publish messages in your scenarios; create a `KafkaConsumer` from the same `bootstrap_servers` to verify consumption.

### Installation

```bash
pip install gherkin-testcontainers-kafka
```

### Example

```gherkin
# features/messaging.feature
Feature: Kafka messaging

  Scenario: Publish a message
    Given a running Kafka broker
    When I send the message "hello"
    Then the topic "greetings" should contain the message
```

```python
# features/steps/messaging_steps.py
from behave import given, when, then
from gherkin_testcontainers import use_container
from kafka import KafkaConsumer

@given("a running Kafka broker")
@use_container("kafka")
def step_kafka(context, kafka_client):
    # kafka_client is a kafka.KafkaProducer
    context.producer = kafka_client
    context.bootstrap_servers = kafka_client.config["bootstrap_servers"]

@when('I send the message "{msg}"')
def step_send(context, msg):
    context.producer.send("greetings", msg.encode())
    context.producer.flush()

@then('the topic "{topic}" should contain the message')
def step_check(context, topic):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=context.bootstrap_servers,
        auto_offset_reset="earliest",
        consumer_timeout_ms=5000,
    )
    messages = [m.value for m in consumer]
    assert len(messages) > 0
```

## Pulsar Integration

The `pulsar` plugin starts an [Apache Pulsar](https://hub.docker.com/r/apachepulsar/pulsar) standalone container and injects a `pulsar.Client`. Use it to create producers and consumers in your scenarios.

### Installation

```bash
pip install gherkin-testcontainers-pulsar
```

### Example

```gherkin
# features/pubsub.feature
Feature: Pulsar pub/sub

  Scenario: Publish and consume a message
    Given a running Pulsar broker
    When I publish "hello" to topic "my-topic"
    Then I should receive "hello" from topic "my-topic"
```

```python
# features/steps/pubsub_steps.py
from behave import given, when, then
from gherkin_testcontainers import use_container

@given("a running Pulsar broker")
@use_container("pulsar")
def step_pulsar(context, pulsar_client):
    # pulsar_client is a pulsar.Client
    context.pulsar = pulsar_client

@when('I publish "{msg}" to topic "{topic}"')
def step_publish(context, msg, topic):
    producer = context.pulsar.create_producer(topic)
    producer.send(msg.encode())

@then('I should receive "{msg}" from topic "{topic}"')
def step_consume(context, msg, topic):
    consumer = context.pulsar.subscribe(topic, "test-sub")
    received = consumer.receive(timeout_millis=5000)
    assert received.data().decode() == msg
    consumer.acknowledge(received)
```

## Azure Event Hubs Integration

The `eventhubs` plugin starts an [Azure Event Hubs emulator](https://github.com/Azure/azure-event-hubs-emulator-installer) container (backed by Azurite for storage) and injects an `azure.eventhub.EventHubProducerClient`. The emulator uses a default namespace (`emulatorNs1`) and event hub (`eh1`), which can be overridden via a custom `Config.json` volume mount.

### Installation

```bash
pip install gherkin-testcontainers-eventhubs
```

### Example

```gherkin
# features/eventhubs.feature
Feature: Azure Event Hubs messaging

  Scenario: Send an event
    Given a running Event Hubs emulator
    When I send the event "hello"
    Then the event hub should have received the event
```

```python
# features/steps/eventhubs_steps.py
from behave import given, when, then
from gherkin_testcontainers import use_container
from azure.eventhub import EventData, EventHubConsumerClient

@given("a running Event Hubs emulator")
@use_container("eventhubs")
def step_eventhubs(context, eventhubs_client):
    # eventhubs_client is an azure.eventhub.EventHubProducerClient
    context.producer = eventhubs_client

@when('I send the event "{msg}"')
def step_send(context, msg):
    with context.producer:
        batch = context.producer.create_batch()
        batch.add(EventData(msg))
        context.producer.send_batch(batch)

@then("the event hub should have received the event")
def step_check(context):
    # consume and verify using EventHubConsumerClient
    pass
```

The default connection string targets the `eh1` event hub in the `emulatorNs1` namespace. To target a different event hub, call `container.get_connection_string(eventhub_name="my-hub")`.

## Development

```bash
git clone <repo>
cd gherkin-testcontainers
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install -e plugins/sqlite -e plugins/postgres -e plugins/mariadb --no-deps -e plugins/oracle -e plugins/kafka -e plugins/pulsar -e plugins/google_pubsub -e plugins/iggy -e plugins/eventhubs

# Run tests
pytest tests/unit/ -v
behave tests/integration/features/
```
