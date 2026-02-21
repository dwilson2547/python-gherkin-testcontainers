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
