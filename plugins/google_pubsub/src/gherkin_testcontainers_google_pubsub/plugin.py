from typing import Any

from testcontainers.google import PubSubContainer

from gherkin_testcontainers.plugin import ContainerPlugin


class GooglePubSubPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "google_pubsub"

    def create_container(self, **kwargs) -> PubSubContainer:
        return PubSubContainer(**kwargs)

    def get_client(self, container: PubSubContainer) -> Any:
        return container.get_publisher()
