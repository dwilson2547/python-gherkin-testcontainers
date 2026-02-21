from gherkin_testcontainers.manager import ContainerManager


def setup_hooks(namespace: dict) -> None:
    """Wire behave lifecycle hooks into the given namespace (environment.py globals)."""

    def before_scenario(context, scenario):
        context.containers = ContainerManager()

    def after_scenario(context, scenario):
        context.containers.stop_all()

    namespace["before_scenario"] = before_scenario
    namespace["after_scenario"] = after_scenario
