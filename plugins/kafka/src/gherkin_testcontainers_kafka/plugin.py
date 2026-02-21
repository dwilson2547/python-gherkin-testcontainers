from typing import Any

from testcontainers.kafka import KafkaContainer

from gherkin_testcontainers.plugin import ContainerPlugin


class KafkaPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "kafka"

    def create_container(self, **kwargs) -> KafkaContainer:
        return KafkaContainer(**kwargs)

    def get_client(self, container: KafkaContainer) -> Any:
        from kafka import KafkaProducer
        bootstrap_servers = container.get_bootstrap_server()
        return KafkaProducer(bootstrap_servers=bootstrap_servers)
