from typing import Any

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from gherkin_testcontainers.plugin import ContainerPlugin

DEFAULT_PULSAR_IMAGE = "apachepulsar/pulsar:3.0.0"
PULSAR_BINARY_PORT = 6650
PULSAR_HTTP_PORT = 8080


class PulsarContainer(DockerContainer):
    """Testcontainer for Apache Pulsar."""

    def __init__(self, image: str = DEFAULT_PULSAR_IMAGE, **kwargs) -> None:
        super().__init__(image, **kwargs)
        self.with_command("bin/pulsar standalone")
        self.with_exposed_ports(PULSAR_BINARY_PORT, PULSAR_HTTP_PORT)

    def get_broker_url(self) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(PULSAR_BINARY_PORT)
        return f"pulsar://{host}:{port}"

    def get_admin_url(self) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(PULSAR_HTTP_PORT)
        return f"http://{host}:{port}"

    def start(self) -> "PulsarContainer":
        super().start()
        wait_for_logs(self, r"messaging service is ready", timeout=60)
        return self


class PulsarPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "pulsar"

    def create_container(self, **kwargs) -> PulsarContainer:
        return PulsarContainer(**kwargs)

    def get_client(self, container: PulsarContainer) -> Any:
        import pulsar
        return pulsar.Client(container.get_broker_url())

    def on_stop(self, container: PulsarContainer) -> None:
        pass
