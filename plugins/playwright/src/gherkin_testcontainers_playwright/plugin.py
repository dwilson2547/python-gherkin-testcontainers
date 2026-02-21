from dataclasses import dataclass, field
from typing import Any

from playwright.sync_api import sync_playwright

from gherkin_testcontainers.plugin import ContainerPlugin


@dataclass
class PlaywrightContainer:
    """Lightweight stand-in for a DockerContainer — manages a Playwright browser instance."""

    browser_type: str = "chromium"
    headless: bool = True
    launch_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self._playwright = None
        self._browser = None

    def start(self):
        self._playwright = sync_playwright().start()
        launcher = getattr(self._playwright, self.browser_type)
        self._browser = launcher.launch(headless=self.headless, **self.launch_kwargs)
        return self

    def stop(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None


class PlaywrightPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "playwright"

    def create_container(self, **kwargs) -> PlaywrightContainer:
        browser_type = kwargs.pop("browser_type", "chromium")
        headless = kwargs.pop("headless", True)
        return PlaywrightContainer(
            browser_type=browser_type,
            headless=headless,
            launch_kwargs=kwargs,
        )

    def get_client(self, container: PlaywrightContainer) -> Any:
        return container._browser.new_page()
