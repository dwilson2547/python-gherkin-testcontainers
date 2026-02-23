import json
import os
import tempfile
from typing import Any

from testcontainers.azurite import AzuriteContainer
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.wait_strategies import PortWaitStrategy

from gherkin_testcontainers.plugin import ContainerPlugin

DEFAULT_EVENTHUBS_IMAGE = "mcr.microsoft.com/azure-messaging/eventhubs-emulator:latest"
EVENTHUBS_AMQP_PORT = 5672
DEFAULT_EVENTHUB_NAMESPACE = "emulatorNs1"
DEFAULT_EVENTHUB_NAME = "eh1"
EVENTHUBS_SHARED_ACCESS_KEY_NAME = "RootManageSharedAccessKey"
EVENTHUBS_SHARED_ACCESS_KEY = "SAS_KEY_VALUE"

DEFAULT_CONFIG = {
    "UserConfig": {
        "NamespaceConfig": [
            {
                "Type": "EventHub",
                "Name": DEFAULT_EVENTHUB_NAMESPACE,
                "Entities": [
                    {
                        "Name": DEFAULT_EVENTHUB_NAME,
                        "PartitionCount": 2,
                        "ConsumerGroups": [
                            {"Name": "cg1"}
                        ],
                    }
                ],
            }
        ],
        "LoggingConfig": {
            "Type": "File"
        },
    }
}


class EventHubsContainer(DockerContainer):
    """Testcontainer for the Azure Event Hubs emulator."""

    def __init__(self, image: str = DEFAULT_EVENTHUBS_IMAGE, **kwargs) -> None:
        super().__init__(image, **kwargs)
        self._eh_network: Network | None = None
        self._azurite: AzuriteContainer | None = None
        self._config_tmp: str | None = None
        self.with_exposed_ports(EVENTHUBS_AMQP_PORT)
        self.with_env("ACCEPT_EULA", "Y")
        self.with_env("BLOB_SERVER", "azurite")
        self.with_env("METADATA_SERVER", "azurite")
        self.waiting_for(PortWaitStrategy(EVENTHUBS_AMQP_PORT))

    def get_connection_string(self, eventhub_name: str = DEFAULT_EVENTHUB_NAME) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(EVENTHUBS_AMQP_PORT)
        return (
            f"Endpoint=sb://{host}:{port};"
            f"SharedAccessKeyName={EVENTHUBS_SHARED_ACCESS_KEY_NAME};"
            f"SharedAccessKey={EVENTHUBS_SHARED_ACCESS_KEY};"
            f"EntityPath={eventhub_name};"
            "UseDevelopmentEmulator=true;"
        )

    def start(self) -> "EventHubsContainer":
        fd, self._config_tmp = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(DEFAULT_CONFIG, f)

        try:
            self._eh_network = Network()
            self._eh_network.create()

            self._azurite = AzuriteContainer()
            self._azurite.with_network(self._eh_network)
            self._azurite.with_network_aliases("azurite")
            self._azurite.start()
        except Exception:
            if self._eh_network is not None:
                self._eh_network.remove()
            if self._config_tmp is not None and os.path.exists(self._config_tmp):
                os.unlink(self._config_tmp)
            raise

        self.with_network(self._eh_network)
        self.with_volume_mapping(
            self._config_tmp,
            "/Eventhubs_Emulator/ConfigFiles/Config.json",
            "ro",
        )
        super().start()
        return self

    def stop(self, force: bool = True, delete_volume: bool = True) -> None:
        try:
            super().stop(force=force, delete_volume=delete_volume)
        finally:
            if self._azurite is not None:
                self._azurite.stop(force=force, delete_volume=delete_volume)
            if self._eh_network is not None:
                self._eh_network.remove()
            if self._config_tmp is not None and os.path.exists(self._config_tmp):
                os.unlink(self._config_tmp)


class EventHubsPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "eventhubs"

    def create_container(self, **kwargs) -> EventHubsContainer:
        return EventHubsContainer(**kwargs)

    def get_client(self, container: EventHubsContainer) -> Any:
        from azure.eventhub import EventHubProducerClient
        return EventHubProducerClient.from_connection_string(container.get_connection_string())
