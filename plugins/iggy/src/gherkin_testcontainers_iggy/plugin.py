from typing import Any

from testcontainers.core.container import DockerContainer

from gherkin_testcontainers.plugin import ContainerPlugin

DEFAULT_IGGY_IMAGE = "iggyrs/iggy:latest"
IGGY_HTTP_PORT = 8080
IGGY_TCP_PORT = 8090


class IggyPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "iggy"

    def create_container(self, **kwargs) -> DockerContainer:
        image = kwargs.pop("image", DEFAULT_IGGY_IMAGE)
        container = DockerContainer(image)
        container.with_exposed_ports(IGGY_HTTP_PORT, IGGY_TCP_PORT)
        return container

    def get_client(self, container: DockerContainer) -> Any:
        from iggy.client import IggyClient
        host = container.get_container_host_ip()
        port = container.get_exposed_port(IGGY_TCP_PORT)
        return IggyClient(host=host, port=int(port))
