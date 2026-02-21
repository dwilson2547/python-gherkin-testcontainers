from typing import Any

from testcontainers.postgres import PostgresContainer

from gherkin_testcontainers.plugin import ContainerPlugin


class PostgresPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "postgres"

    def create_container(self, **kwargs) -> PostgresContainer:
        return PostgresContainer(**kwargs)

    def get_client(self, container: PostgresContainer) -> Any:
        import psycopg
        url = container.get_connection_url()
        return psycopg.connect(url)
