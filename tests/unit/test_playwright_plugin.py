# tests/unit/test_playwright_plugin.py
from unittest.mock import MagicMock, patch

from gherkin_testcontainers.plugin import ContainerPlugin
from gherkin_testcontainers_playwright.plugin import PlaywrightContainer, PlaywrightPlugin


def test_playwright_plugin_is_a_container_plugin():
    plugin = PlaywrightPlugin()
    assert isinstance(plugin, ContainerPlugin)


def test_playwright_plugin_name():
    plugin = PlaywrightPlugin()
    assert plugin.name == "playwright"


def test_playwright_plugin_create_container_defaults():
    plugin = PlaywrightPlugin()
    container = plugin.create_container()
    assert isinstance(container, PlaywrightContainer)
    assert container.browser_type == "chromium"
    assert container.headless is True
    assert container.launch_kwargs == {}


def test_playwright_plugin_create_container_custom_browser():
    plugin = PlaywrightPlugin()
    container = plugin.create_container(browser_type="firefox", headless=False)
    assert container.browser_type == "firefox"
    assert container.headless is False


def test_playwright_plugin_create_container_passes_extra_kwargs():
    plugin = PlaywrightPlugin()
    container = plugin.create_container(slow_mo=50)
    assert container.launch_kwargs == {"slow_mo": 50}


def test_playwright_plugin_get_client_returns_new_page():
    plugin = PlaywrightPlugin()
    mock_page = MagicMock()
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page

    container = PlaywrightContainer()
    container._browser = mock_browser

    client = plugin.get_client(container)

    mock_browser.new_page.assert_called_once()
    assert client is mock_page


def test_playwright_container_start_launches_browser():
    with patch("gherkin_testcontainers_playwright.plugin.sync_playwright") as mock_sync_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser

        container = PlaywrightContainer(browser_type="chromium", headless=True)
        result = container.start()

        mock_playwright.chromium.launch.assert_called_once_with(headless=True)
        assert container._browser is mock_browser
        assert result is container


def test_playwright_container_stop_closes_browser():
    mock_browser = MagicMock()
    mock_playwright = MagicMock()

    container = PlaywrightContainer()
    container._browser = mock_browser
    container._playwright = mock_playwright

    container.stop()

    mock_browser.close.assert_called_once()
    mock_playwright.stop.assert_called_once()
    assert container._browser is None
    assert container._playwright is None


def test_playwright_container_stop_is_safe_when_not_started():
    container = PlaywrightContainer()
    # Should not raise
    container.stop()
