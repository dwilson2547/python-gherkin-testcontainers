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
