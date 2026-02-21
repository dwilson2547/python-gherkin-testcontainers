from typing import Any

from testcontainers.oracle import OracleDbContainer

from gherkin_testcontainers.plugin import ContainerPlugin


class OraclePlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "oracle"

    def create_container(self, **kwargs) -> OracleDbContainer:
        return OracleDbContainer(**kwargs)

    def get_client(self, container: OracleDbContainer) -> Any:
        import oracledb
        return oracledb.connect(
            user=container.username,
            password=container.password,
            dsn=f"{container.get_container_host_ip()}:{container.get_exposed_port(1521)}/{container.dbname}",
        )
