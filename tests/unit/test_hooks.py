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
