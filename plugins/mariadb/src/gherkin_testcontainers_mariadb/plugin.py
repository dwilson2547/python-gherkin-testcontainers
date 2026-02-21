from typing import Any

from testcontainers.mysql import MySqlContainer

from gherkin_testcontainers.plugin import ContainerPlugin

DEFAULT_MARIADB_IMAGE = "mariadb:11"


class MariadbPlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "mariadb"

    def create_container(self, **kwargs) -> MySqlContainer:
        if "image" not in kwargs:
            kwargs["image"] = DEFAULT_MARIADB_IMAGE
        return MySqlContainer(**kwargs)

    def get_client(self, container: MySqlContainer) -> Any:
        import pymysql
        url = container.get_connection_url()
        import sqlalchemy
        engine = sqlalchemy.create_engine(url)
        return engine.connect()
