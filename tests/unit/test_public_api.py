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
