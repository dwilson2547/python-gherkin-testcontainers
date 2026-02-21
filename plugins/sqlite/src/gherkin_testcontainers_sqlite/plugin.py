import sqlite3
import tempfile
from dataclasses import dataclass, field
from typing import Any

from gherkin_testcontainers.plugin import ContainerPlugin


@dataclass
class SqliteContainer:
    """Lightweight stand-in for a DockerContainer — just holds a temp file path."""
    db_path: str = field(default="")

    def start(self):
        if not self.db_path:
            self.db_path = tempfile.mktemp(suffix=".db")
        return self

    def stop(self):
        import os
        if self.db_path and os.path.exists(self.db_path):
            os.remove(self.db_path)


class SqlitePlugin(ContainerPlugin):

    @property
    def name(self) -> str:
        return "sqlite"

    def create_container(self, **kwargs) -> SqliteContainer:
        return SqliteContainer(**kwargs)

    def get_client(self, container: SqliteContainer) -> Any:
        return sqlite3.connect(container.db_path)
