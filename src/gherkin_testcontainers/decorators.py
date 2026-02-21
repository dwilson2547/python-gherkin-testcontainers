import functools
from typing import Any, Callable


def use_container(plugin_name: str, **container_kwargs) -> Callable:
    """Decorator that injects a container client into a behave step function.

    The client is injected as a keyword argument named '{plugin_name}_client'.
    """
    client_param = f"{plugin_name}_client"

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(context, *args, **kwargs):
            client = context.containers.get_client(
                plugin_name, **container_kwargs
            )
            kwargs[client_param] = client
            return fn(context, *args, **kwargs)

        return wrapper

    return decorator
